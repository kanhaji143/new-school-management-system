"""Assessments API views."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import IsAuthenticatedInInstitution, IsCoordinator
from common.views import InstitutionAwareMixin, TenantModelViewSet

from . import models, serializers, services
from . import importers


class AssessmentRuleMixin:
    @staticmethod
    def rule_error(message):
        return Response(
            {"success": False, "message": message, "errors": {"fieldErrors": {}, "formErrors": [message]}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code >= 400:
            return response
        return Response({"success": True, "data": response.data}, status=response.status_code)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        if response.status_code >= 400:
            return response
        return Response({"success": True, "data": response.data})

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code >= 400:
            return response
        return Response({"success": True, "data": response.data})

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        if response.status_code >= 400:
            return response
        return Response({"success": True, "data": response.data})


class QuestionBankViewSet(AssessmentRuleMixin, TenantModelViewSet):
    queryset = models.QuestionBank.objects.all()
    serializer_class = serializers.QuestionBankSerializer
    filterset_fields = ("subject",)
    search_fields = ("name",)
    write_permission_class = IsCoordinator

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedInInstitution()]
        return [IsCoordinator()]

    @action(detail=True, methods=["get", "post"], url_path="questions")
    def questions(self, request, pk=None):
        bank = self.get_object()
        if request.method == "GET":
            data = serializers.QuestionSerializer(
                bank.questions.all(), many=True, context=self.get_serializer_context()
            ).data
            return Response({"success": True, "data": data})
        payload = serializers.QuestionSerializer(data=request.data, context=self.get_serializer_context())
        payload.is_valid(raise_exception=True)
        question = payload.save(institution_id=bank.institution_id, bank=bank)
        data = serializers.QuestionSerializer(question, context=self.get_serializer_context()).data
        return Response({"success": True, "data": data}, status=status.HTTP_201_CREATED)


class QuestionViewSet(AssessmentRuleMixin, TenantModelViewSet):
    queryset = models.Question.objects.all()
    serializer_class = serializers.QuestionSerializer
    filterset_fields = ("bank", "question_type", "difficulty")
    search_fields = ("text",)
    write_permission_class = IsCoordinator

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedInInstitution()]
        return [IsCoordinator()]


class GradeScaleViewSet(AssessmentRuleMixin, TenantModelViewSet):
    queryset = models.GradeScale.objects.all()
    serializer_class = serializers.GradeScaleSerializer
    write_permission_class = IsCoordinator

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedInInstitution()]
        return [IsCoordinator()]


class AssessmentViewSet(AssessmentRuleMixin, TenantModelViewSet):
    queryset = models.Assessment.objects.all()
    serializer_class = serializers.AssessmentSerializer
    filterset_fields = ("assessment_type", "subject", "section", "academic_year", "term", "status")
    search_fields = ("title",)
    write_permission_class = IsCoordinator

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedInInstitution()]
        return [IsCoordinator()]

    def perform_create(self, serializer):
        serializer.save(institution_id=self.request.institution_id, created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        assessment = self.get_object()
        payload = serializers.AssignStudentsSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        payload.is_valid(raise_exception=True)
        try:
            result = services.assign_students(assessment, payload.validated_data["students"])
        except services.AssessmentError as exc:
            return self.rule_error(exc.message)
        return Response({"success": True, "message": "Students assigned.", "data": result})

    @action(detail=True, methods=["post"], url_path="question-imports/preview")
    def preview_question_import(self, request, pk=None):
        assessment = self.get_object()
        payload = serializers.QuestionImportPreviewSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            question_import = importers.prepare_question_import(
                assessment,
                text=payload.validated_data.get("text", ""),
                upload=payload.validated_data.get("file"),
                actor=request.user,
            )
        except importers.QuestionImportError as exc:
            return self.rule_error(str(exc))
        return Response(
            {"success": True, "data": serializers.QuestionImportSerializer(question_import).data},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="marks")
    def marks(self, request, pk=None):
        assessment = self.get_object()
        payload = serializers.MarksBulkSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            result = services.bulk_marks(assessment, payload.validated_data["records"], marked_by=request.user)
        except services.AssessmentError as exc:
            return self.rule_error(exc.message)
        return Response({"success": True, "message": "Marks saved.", "data": result})

    @action(detail=True, methods=["get"], url_path="results")
    def results(self, request, pk=None):
        assessment = self.get_object()
        data = services.compute_results(assessment)
        return Response({"success": True, "data": data})


class AssessmentQuestionViewSet(AssessmentRuleMixin, TenantModelViewSet):
    queryset = models.AssessmentQuestion.objects.all()
    serializer_class = serializers.AssessmentQuestionSerializer
    filterset_fields = ("assessment", "question")
    write_permission_class = IsCoordinator

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedInInstitution()]
        return [IsCoordinator()]


class StudentAssessmentViewSet(AssessmentRuleMixin, TenantModelViewSet):
    queryset = models.StudentAssessment.objects.all()
    serializer_class = serializers.StudentAssessmentSerializer
    filterset_fields = ("assessment", "student", "status")
    write_permission_class = IsCoordinator

    def get_permissions(self):
        if self.action in ("list", "retrieve", "mine", "submit"):
            return [IsAuthenticatedInInstitution()]
        return [IsCoordinator()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.has_any_role("STUDENT"):
            queryset = queryset.filter(student__user=self.request.user)
        return queryset

    @action(detail=False, methods=["get"])
    def mine(self, request):
        student_rows = self.get_queryset().filter(student__user=request.user).select_related(
            "assessment", "assessment__subject", "student__user"
        )
        data = self.get_serializer(student_rows, many=True).data
        return Response({"success": True, "data": data})

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        if not request.user.has_any_role("STUDENT"):
            return Response({"success": False, "message": "Student account required."}, status=403)
        assignment = self.get_object()
        payload = serializers.StudentAnswersSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            assignment = services.submit_student_answers(
                assignment, request.user, payload.validated_data["answers"]
            )
        except services.AssessmentError as exc:
            return self.rule_error(exc.message)
        return Response({
            "success": True,
            "message": "Assessment submitted to your teacher.",
            "data": self.get_serializer(assignment).data,
        })


class QuestionImportViewSet(AssessmentRuleMixin, InstitutionAwareMixin, viewsets.ReadOnlyModelViewSet):
    queryset = models.QuestionImport.objects.select_related("assessment")
    serializer_class = serializers.QuestionImportSerializer
    filterset_fields = ("assessment", "status")
    permission_classes = [IsCoordinator]
    write_permission_class = IsCoordinator

    def get_permissions(self):
        return [IsCoordinator()]

    def get_queryset(self):
        return models.QuestionImport.objects.filter(
            institution_id=self.request.institution_id
        ).select_related("assessment")

    @action(detail=True, methods=["post"])
    def refresh(self, request, pk=None):
        question_import = self.get_object()
        payload = serializers.QuestionImportRefreshSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            question_import = importers.refresh_question_import(
                question_import,
                text=payload.validated_data.get("text", ""),
                upload=payload.validated_data.get("file"),
            )
        except importers.QuestionImportError as exc:
            return self.rule_error(str(exc))
        return Response({"success": True, "data": self.serializer_class(question_import).data})

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        question_import = self.get_object()
        try:
            question_import = importers.confirm_question_import(question_import)
        except importers.QuestionImportError as exc:
            return self.rule_error(str(exc))
        return Response({
            "success": True,
            "message": f"Imported {question_import.imported_count} questions into the assessment.",
            "data": self.serializer_class(question_import, context=self.get_serializer_context()).data,
        })
