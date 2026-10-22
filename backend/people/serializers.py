"""People API serializers.

Serializers whitelist fields explicitly to prevent mass assignment (OWASP).
"""
from rest_framework import serializers

from academics.models import Course, Section
from common.serializers import TenantRelatedField, UserSummarySerializer
from users.models import User

from . import services
from .models import Guardian, PersonBase, Student, StudentGuardian, Teacher


class PersonUserSerializer(UserSummarySerializer):
    """User payload embedded in every person profile."""

    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)


class StudentSerializer(serializers.ModelSerializer):
    user = PersonUserSerializer(read_only=True)
    section_detail = serializers.SerializerMethodField()
    course_detail = serializers.SerializerMethodField()
    whatsapp_contacts = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = (
            "id", "roll_number", "admission_number", "admission_date",
            "user", "date_of_birth", "gender", "address", "blood_group", "photo",
            "section", "section_detail", "course", "course_detail", "whatsapp_contacts",
            "status", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_section_detail(self, obj):
        if not obj.section:
            return None
        return {
            "id": obj.section.id,
            "name": obj.section.name,
            "school_class": obj.section.school_class.name,
        }

    def get_course_detail(self, obj):
        if not obj.course:
            return None
        return {"id": obj.course.id, "code": obj.course.code, "name": obj.course.name}

    def get_whatsapp_contacts(self, obj):
        links = StudentGuardian.all_objects.filter(
            institution_id=obj.institution_id, student=obj
        ).select_related("guardian__user").order_by("-is_primary", "id")
        contacts = []
        seen = set()
        for link in links:
            user = link.guardian.user
            phone = (user.phone or "").strip()
            if phone and phone not in seen:
                contacts.append({
                    "name": user.full_name,
                    "phone": phone,
                    "relation": link.guardian.get_relation_display(),
                    "recipient_type": "PARENT",
                    "is_primary": link.is_primary,
                })
                seen.add(phone)
        student_phone = (obj.user.phone or "").strip()
        if student_phone and student_phone not in seen:
            contacts.append({
                "name": obj.user.full_name,
                "phone": student_phone,
                "relation": "Student",
                "recipient_type": "STUDENT",
                "is_primary": not contacts,
            })
        return contacts

    def validate_section(self, value):
        self._check_tenant(value)
        return value

    def validate_course(self, value):
        self._check_tenant(value)
        return value

    def _check_tenant(self, obj):
        institution_id = self.context.get("institution_id")
        if institution_id is not None and obj.institution_id != institution_id:
            raise serializers.ValidationError("Object belongs to another institution.")


class TeacherSerializer(serializers.ModelSerializer):
    user = PersonUserSerializer(read_only=True)
    class_subject_count = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = (
            "id", "employee_id", "department", "qualification",
            "max_periods_per_week", "joining_date", "status",
            "user", "date_of_birth", "gender", "address", "blood_group", "photo",
            "class_subject_count", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_class_subject_count(self, obj):
        return obj.class_subjects.count()


class GuardianSerializer(serializers.ModelSerializer):
    user = PersonUserSerializer(read_only=True)
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Guardian
        fields = (
            "id", "relation", "occupation",
            "user", "date_of_birth", "gender", "address", "blood_group", "photo",
            "student_count", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_student_count(self, obj):
        return obj.student_links.count()


class StudentGuardianSerializer(serializers.ModelSerializer):
    student_detail = StudentSerializer(source="student", read_only=True)
    guardian_detail = GuardianSerializer(source="guardian", read_only=True)
    student = TenantRelatedField(
        queryset=Student.all_objects.all(), required=False, allow_null=False
    )
    guardian = TenantRelatedField(
        queryset=Guardian.all_objects.all(), required=False, allow_null=False
    )

    class Meta:
        model = StudentGuardian
        fields = (
            "id", "student", "student_detail", "guardian", "guardian_detail",
            "is_primary", "is_emergency_contact", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


# --------------------------------------------------------------------------------------
# Create payloads: these create the login account together with the profile.
# --------------------------------------------------------------------------------------
class PersonCreateMixin(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, required=False, min_length=8,
                                     help_text="Omit to auto-generate a random password.")
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(
        choices=PersonBase.GENDER_CHOICES, required=False, allow_blank=True
    )
    address = serializers.CharField(required=False, allow_blank=True)
    blood_group = serializers.CharField(max_length=5, required=False, allow_blank=True)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def _institution_id(self):
        institution_id = self.context.get("institution_id")
        if institution_id is None:
            raise serializers.ValidationError(
                {"institution": "No institution in request context."}
            )
        return institution_id


class StudentCreateSerializer(PersonCreateMixin):
    roll_number = serializers.CharField(max_length=30)
    admission_number = serializers.CharField(max_length=30)
    admission_date = serializers.DateField(required=False, allow_null=True)
    section = TenantRelatedField(
        queryset=Section.all_objects.all(), required=False, allow_null=True
    )
    course = TenantRelatedField(
        queryset=Course.all_objects.all(), required=False, allow_null=True
    )
    status = serializers.ChoiceField(
        choices=Student.Status.choices, required=False, default=Student.Status.ACTIVE
    )

    def validate_admission_number(self, value):
        if Student.all_objects.filter(admission_number=value).exists():
            raise serializers.ValidationError("Admission number already in use.")
        return value

    def create(self, validated_data):
        section = validated_data.pop("section", None)
        course = validated_data.pop("course", None)
        email = validated_data.pop("email")
        password = validated_data.pop("password", None)
        first_name = validated_data.pop("first_name", "")
        last_name = validated_data.pop("last_name", "")
        phone = validated_data.pop("phone", "")
        institution_id = self._institution_id()
        return services.create_student(
            institution_id, email, password=password,
            first_name=first_name, last_name=last_name, phone=phone,
            section=section, course=course, **validated_data
        )


class TeacherCreateSerializer(PersonCreateMixin):
    employee_id = serializers.CharField(max_length=30)
    department = serializers.CharField(max_length=120, required=False, allow_blank=True)
    qualification = serializers.CharField(max_length=200, required=False, allow_blank=True)
    max_periods_per_week = serializers.IntegerField(required=False, default=30, min_value=0)
    joining_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=Teacher.Status.choices, required=False, default=Teacher.Status.ACTIVE
    )

    def validate_employee_id(self, value):
        if Teacher.all_objects.filter(employee_id=value).exists():
            raise serializers.ValidationError("Employee ID already in use.")
        return value

    def create(self, validated_data):
        email = validated_data.pop("email")
        password = validated_data.pop("password", None)
        first_name = validated_data.pop("first_name", "")
        last_name = validated_data.pop("last_name", "")
        phone = validated_data.pop("phone", "")
        institution_id = self._institution_id()
        return services.create_teacher(
            institution_id, email, password=password,
            first_name=first_name, last_name=last_name, phone=phone,
            **validated_data
        )


class GuardianCreateSerializer(PersonCreateMixin):
    relation = serializers.ChoiceField(choices=Guardian.RELATION_CHOICES)
    occupation = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def create(self, validated_data):
        email = validated_data.pop("email")
        password = validated_data.pop("password", None)
        first_name = validated_data.pop("first_name", "")
        last_name = validated_data.pop("last_name", "")
        phone = validated_data.pop("phone", "")
        institution_id = self._institution_id()
        return services.create_guardian(
            institution_id, email, password=password,
            first_name=first_name, last_name=last_name, phone=phone,
            **validated_data
        )
