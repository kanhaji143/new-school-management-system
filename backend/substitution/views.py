"""Substitution API views."""
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from common.permissions import IsAuthenticatedInInstitution, IsCoordinator
from common.views import TenantModelViewSet
from people.models import Teacher

from . import models, serializers, services


class SubstitutionRuleMixin:
    @staticmethod
    def rule_error(message):
        return Response(
            {
                "success": False,
                "message": message,
                "errors": {"fieldErrors": {}, "formErrors": [message]},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code >= 400:
            return response
        return Response(
            {"success": True, "data": response.data}, status=response.status_code
        )

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


class SubstitutionRequestViewSet(SubstitutionRuleMixin, TenantModelViewSet):
    queryset = models.SubstitutionRequest.objects.all()
    serializer_class = serializers.SubstitutionRequestSerializer
    create_serializer_class = serializers.SubstitutionRequestCreateSerializer
    filterset_fields = ("status", "absent_teacher", "date")
    search_fields = ("absent_teacher__employee_id", "reason")
    ordering_fields = ("date", "created_at")

    write_permission_class = IsCoordinator

    def get_permissions(self):
        # Any authenticated member may file a request or read; coordinator-only
        # actions for generate/approve/handover/outcome/cancel.
        if self.action in ("list", "retrieve", "create"):
            return [IsAuthenticatedInInstitution()]
        return [IsCoordinator()]

    def get_serializer_class(self):
        if self.action == "create":
            return self.create_serializer_class
        return self.serializer_class

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and not user.has_any_role(
            "COORDINATOR", "SCHOOL_ADMIN", "SUPER_ADMIN"
        ):
            # Teachers see requests where they are the absent teacher.
            queryset = queryset.filter(absent_teacher__user=user)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(institution_id=self.request.institution_id, created_by=user)

    # --------------------------------------------------------------- generate
    @action(detail=True, methods=["post"])
    def recommend(self, request, pk=None):
        substitution_request = self.get_object()
        if substitution_request.status not in (
            models.SubstitutionRequest.Status.OPEN,
            models.SubstitutionRequest.Status.PROPOSED,
        ):
            return self.rule_error("Recommendations can only be generated for open requests.")
        payload_serializer = serializers.RecommendPayloadSerializer(data=request.data)
        payload_serializer.is_valid(raise_exception=True)
        limit = payload_serializer.validated_data.get("limit", 3)
        strict = payload_serializer.validated_data.get("strict_subject", True)

        # Temporarily toggle strict_subject by filtering candidates manually.
        original = services.eligible_teachers
        if not strict:
            def _loose(req, *, strict_subject=True):
                return original(req, strict_subject=False)
            services.eligible_teachers = _loose
        try:
            scored = services.recommend(substitution_request, limit=limit)
        finally:
            services.eligible_teachers = original

        substitution_request.status = models.SubstitutionRequest.Status.PROPOSED
        substitution_request.save(update_fields=["status", "updated_at"])
        data = serializers.SubstituteRecommendationSerializer(
            substitution_request.recommendations.all(), many=True, context=self.get_serializer_context()
        ).data
        return Response({"success": True, "data": data})

    # --------------------------------------------------------------- list
    @action(detail=True, methods=["get"], url_path="recommendations")
    def recommendations(self, request, pk=None):
        substitution_request = self.get_object()
        recs = substitution_request.recommendations.all()
        if not recs.exists() and substitution_request.status in (
            models.SubstitutionRequest.Status.OPEN,
            models.SubstitutionRequest.Status.PROPOSED,
        ):
            services.recommend(substitution_request, limit=3)
            substitution_request.status = models.SubstitutionRequest.Status.PROPOSED
            substitution_request.save(update_fields=["status", "updated_at"])
            recs = substitution_request.recommendations.all()
        data = serializers.SubstituteRecommendationSerializer(
            recs, many=True, context=self.get_serializer_context()
        ).data
        return Response({"success": True, "data": data})

    # --------------------------------------------------------------- assign
    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        substitution_request = self.get_object()
        if substitution_request.status not in (
            models.SubstitutionRequest.Status.OPEN,
            models.SubstitutionRequest.Status.PROPOSED,
        ):
            return self.rule_error("This request is no longer assignable.")

        payload = serializers.AssignSubstituteSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        substitute_teacher = data.get("substitute_teacher")
        recommendation_id = data.get("recommendation")
        if recommendation_id and not substitute_teacher:
            try:
                rec = models.SubstituteRecommendation.objects.get(
                    pk=recommendation_id, request=substitution_request
                )
            except models.SubstituteRecommendation.DoesNotExist:
                return self.rule_error("Recommendation not found for this request.")
            substitute_teacher = rec.teacher

        if models.SubstituteAssignment.objects.filter(request=substitution_request).exists():
            return self.rule_error("An assignment already exists for this request.")

        assignment = models.SubstituteAssignment.objects.create(
            institution_id=substitution_request.institution_id,
            request=substitution_request,
            substitute_teacher=substitute_teacher,
            status=models.SubstituteAssignment.Status.APPROVED,
            approved_by=request.user,
            approved_at=timezone.now(),
        )
        substitution_request.status = models.SubstitutionRequest.Status.APPROVED
        substitution_request.save(update_fields=["status", "updated_at"])

        data = serializers.SubstituteAssignmentSerializer(
            assignment, context=self.get_serializer_context()
        ).data
        return Response({"success": True, "message": "Substitute assigned.", "data": data})

    # --------------------------------------------------------------- handover
    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser, JSONParser])
    def handover(self, request, pk=None):
        substitution_request = self.get_object()
        assignment = getattr(substitution_request, "assignment", None)
        if assignment is None:
            return self.rule_error("Assign a substitute before creating a handover.")

        payload = serializers.HandoverPayloadSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        notes = payload.validated_data.get("notes", "")

        material, _ = models.HandoverMaterial.objects.get_or_create(
            assignment=assignment,
            defaults={
                "institution_id": substitution_request.institution_id,
                "notes": notes,
                "prepared_by": request.user,
            },
        )
        if notes:
            material.notes = notes
            material.prepared_by = request.user
            material.save(update_fields=["notes", "prepared_by", "updated_at"])

        uploaded = request.FILES.get("file")
        if uploaded:
            models.HandoverAttachment.objects.create(
                institution_id=substitution_request.institution_id,
                material=material,
                file=uploaded,
                filename=uploaded.name,
                uploaded_by=request.user,
            )

        data = serializers.HandoverMaterialSerializer(
            material, context=self.get_serializer_context()
        ).data
        return Response({"success": True, "message": "Handover saved.", "data": data})

    # --------------------------------------------------------------- outcome
    @action(detail=True, methods=["post"])
    def outcome(self, request, pk=None):
        substitution_request = self.get_object()
        assignment = getattr(substitution_request, "assignment", None)
        if assignment is None:
            return self.rule_error("Assign a substitute before recording an outcome.")

        payload = serializers.OutcomePayloadSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        outcome, _ = models.ClassOutcome.objects.get_or_create(
            assignment=assignment,
            defaults={
                "institution_id": substitution_request.institution_id,
                "status": data["status"],
                "notes": data.get("notes", ""),
                "recorded_by": request.user,
            },
        )
        outcome.status = data["status"]
        outcome.notes = data.get("notes", "")
        outcome.recorded_by = request.user
        outcome.save(update_fields=["status", "notes", "recorded_by"])

        assignment.status = models.SubstituteAssignment.Status.COMPLETED
        assignment.save(update_fields=["status", "updated_at"])
        substitution_request.status = models.SubstitutionRequest.Status.COMPLETED
        substitution_request.save(update_fields=["status", "updated_at"])

        data = serializers.ClassOutcomeSerializer(
            outcome, context=self.get_serializer_context()
        ).data
        return Response({"success": True, "message": "Outcome recorded.", "data": data})

    # --------------------------------------------------------------- cancel
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        substitution_request = self.get_object()
        if substitution_request.status in (
            models.SubstitutionRequest.Status.COMPLETED,
            models.SubstitutionRequest.Status.CANCELLED,
        ):
            return self.rule_error("This request can no longer be cancelled.")
        substitution_request.status = models.SubstitutionRequest.Status.CANCELLED
        substitution_request.save(update_fields=["status", "updated_at"])
        return Response({"success": True, "message": "Request cancelled."})
