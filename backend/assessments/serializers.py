"""Assessments serializers."""
from decimal import Decimal
from rest_framework import serializers

from common.serializers import TenantRelatedField, UserSummarySerializer
from academics.models import AcademicYear, Section, Subject, Term
from people.models import Student

from . import models


class SubjectMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ("id", "code", "name")


class SectionMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ("id", "name")


class AcademicYearMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ("id", "name")


class TermMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = ("id", "name")


class StudentMiniSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Student
        fields = ("id", "roll_number", "full_name")


# ---------------------------------------------------------------- question bank
class QuestionBankSerializer(serializers.ModelSerializer):
    subject_detail = SubjectMiniSerializer(source="subject", read_only=True)
    question_count = serializers.IntegerField(source="questions.count", read_only=True)
    subject = TenantRelatedField(queryset=Subject.all_objects.all(), required=False, allow_null=True)

    class Meta:
        model = models.QuestionBank
        fields = ("id", "name", "subject", "subject_detail", "description", "question_count", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class QuestionSerializer(serializers.ModelSerializer):
    bank = TenantRelatedField(queryset=models.QuestionBank.all_objects.all(), required=False)

    class Meta:
        model = models.Question
        fields = ("id", "bank", "question_type", "text", "marks", "options", "correct_answer", "difficulty", "vocabulary_terms", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


# ---------------------------------------------------------------- grade scale
class GradeScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GradeScale
        fields = ("id", "grade", "min_mark", "max_mark", "remark", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


# ---------------------------------------------------------------- assessment
class AssessmentSerializer(serializers.ModelSerializer):
    subject_detail = SubjectMiniSerializer(source="subject", read_only=True)
    section_detail = SectionMiniSerializer(source="section", read_only=True)
    academic_year_detail = AcademicYearMiniSerializer(source="academic_year", read_only=True)
    term_detail = TermMiniSerializer(source="term", read_only=True)
    created_by_detail = UserSummarySerializer(source="created_by", read_only=True)
    question_count = serializers.IntegerField(source="questions.count", read_only=True)
    marks_entered = serializers.IntegerField(source="student_marks.count", read_only=True)
    subject = TenantRelatedField(queryset=Subject.all_objects.all(), required=False, allow_null=True)
    section = TenantRelatedField(queryset=Section.all_objects.all(), required=False, allow_null=True)
    academic_year = TenantRelatedField(queryset=AcademicYear.all_objects.all())
    term = TenantRelatedField(queryset=Term.all_objects.all(), required=False, allow_null=True)

    class Meta:
        model = models.Assessment
        fields = (
            "id", "title", "assessment_type", "subject", "subject_detail", "section",
            "section_detail", "course", "academic_year", "academic_year_detail", "term",
            "term_detail", "date", "total_marks", "pass_marks", "status", "created_by_detail",
            "question_count", "marks_entered", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")


class AssessmentStudentViewSerializer(serializers.ModelSerializer):
    subject_detail = SubjectMiniSerializer(source="subject", read_only=True)

    class Meta:
        model = models.Assessment
        fields = ("id", "title", "assessment_type", "date", "subject_detail", "total_marks", "pass_marks", "status")


# ---------------------------------------------------------------- assessment question
class AssessmentQuestionSerializer(serializers.ModelSerializer):
    question_detail = QuestionSerializer(source="question", read_only=True)
    assessment = TenantRelatedField(queryset=models.Assessment.all_objects.all())
    question = TenantRelatedField(queryset=models.Question.all_objects.all())

    class Meta:
        model = models.AssessmentQuestion
        fields = ("id", "assessment", "question", "question_detail", "marks_override")
        read_only_fields = ("id",)


# ---------------------------------------------------------------- student assessment (marks)
class StudentAssessmentSerializer(serializers.ModelSerializer):
    student_detail = StudentMiniSerializer(source="student", read_only=True)
    assessment_detail = AssessmentStudentViewSerializer(source="assessment", read_only=True)
    questions = serializers.SerializerMethodField()
    assessment = TenantRelatedField(queryset=models.Assessment.all_objects.all())
    student = TenantRelatedField(queryset=Student.all_objects.all())

    class Meta:
        model = models.StudentAssessment
        fields = (
            "id", "assessment", "assessment_detail", "student", "student_detail", "obtained_marks", "grade",
            "remarks", "answers", "questions", "status", "submitted_at", "created_at", "updated_at",
        )
        read_only_fields = ("id", "grade", "answers", "questions", "created_at", "updated_at")

    def get_questions(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated or not user.has_any_role("STUDENT"):
            return []
        if obj.student.user_id != user.id:
            return []
        return [
            {
                "id": link.question_id,
                "question_type": link.question.question_type,
                "text": link.question.text,
                "marks": link.marks_override or link.question.marks,
                "options": link.question.options or [],
                "vocabulary_terms": link.question.vocabulary_terms or [],
            }
            for link in obj.assessment.questions.select_related("question").all()
        ]


class MarksRecordSerializer(serializers.Serializer):
    student = TenantRelatedField(queryset=Student.all_objects.all())
    obtained_marks = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, allow_null=True)
    remarks = serializers.CharField(required=False, allow_blank=True, default="")
    status = serializers.ChoiceField(
        choices=models.StudentAssessment.Status.choices, default=models.StudentAssessment.Status.GRADED
    )


class MarksBulkSerializer(serializers.Serializer):
    records = MarksRecordSerializer(many=True)

    def validate_records(self, value):
        if not value:
            raise serializers.ValidationError("Provide at least one student record.")
        student_ids = [r["student"].id for r in value]
        if len(student_ids) != len(set(student_ids)):
            raise serializers.ValidationError("Duplicate students in the marks entry.")
        return value


class AssignStudentsSerializer(serializers.Serializer):
    students = TenantRelatedField(queryset=Student.all_objects.all(), many=True)

    def validate_students(self, value):
        if not value:
            raise serializers.ValidationError("Select at least one student.")
        ids = [student.id for student in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("A student was selected more than once.")
        return value


class StudentAnswersSerializer(serializers.Serializer):
    answers = serializers.DictField(child=serializers.JSONField())


class QuestionImportPreviewSerializer(serializers.Serializer):
    file = serializers.FileField(required=False, allow_null=True)
    text = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_file(self, value):
        allowed = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt"}
        from pathlib import Path

        suffix = Path(value.name).suffix.lower()
        if suffix not in allowed:
            raise serializers.ValidationError("Supported formats: PDF, JPEG/PNG, DOC/DOCX, XLS/XLSX, CSV and TXT.")
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Maximum upload size is 10 MB.")
        return value

    def validate(self, attrs):
        if not attrs.get("file") and not attrs.get("text", "").strip():
            raise serializers.ValidationError("Paste question text or choose a file.")
        return attrs


class QuestionImportRefreshSerializer(serializers.Serializer):
    file = serializers.FileField(required=False, allow_null=True)
    text = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_file(self, value):
        from pathlib import Path

        allowed = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt"}
        if Path(value.name).suffix.lower() not in allowed:
            raise serializers.ValidationError("Unsupported file extension.")
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Maximum upload size is 10 MB.")
        return value

    def validate(self, attrs):
        if not attrs.get("file") and not attrs.get("text", "").strip():
            raise serializers.ValidationError("Paste the text to add or choose a file.")
        return attrs


class QuestionImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.QuestionImport
        fields = (
            "id", "assessment", "original_file_name", "pasted_text", "extraction_warning",
            "parsed_questions", "status", "imported_count", "created_at",
        )
        read_only_fields = fields
