"""Timetable API views."""
from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from common.views import TenantModelViewSet

from . import models, serializers, services


def _handle_rule_error(view, exc):
    """Convert a services.BusinessRuleError into a 400 with a clean message."""
    return Response(
        {"success": False, "message": exc.message,
         "errors": {"fieldErrors": {}, "formErrors": [exc.message]}},
        status=status.HTTP_400_BAD_REQUEST,
    )


class PeriodTemplateViewSet(TenantModelViewSet):
    queryset = models.PeriodTemplate.objects.all()
    serializer_class = serializers.PeriodTemplateSerializer
    filterset_fields = ("day",)
    search_fields = ("name",)


class TimetableViewSet(TenantModelViewSet):
    queryset = models.Timetable.objects.all()
    create_serializer_class = serializers.TimetableWriteSerializer
    read_serializer_class = serializers.TimetableSerializer
    filterset_fields = ("status", "section", "course", "academic_year", "term", "version")
    search_fields = ()

    def get_serializer_class(self):
        if self.action == "create":
            return self.create_serializer_class
        return self.read_serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(institution_id=request.institution_id)
        data = self.read_serializer_class(
            instance, context=self.get_serializer_context()
        ).data
        return Response({"success": True, "data": data}, status=status.HTTP_201_CREATED)

    @staticmethod
    def conflict_report(conflicts, total_entries):
        """Serialize a conflict scan into the shape the UI consumes."""
        severities = models.TimetableConflict.Severity
        hard = [c for c in conflicts if c.severity == severities.HARD]
        soft = [c for c in conflicts if c.severity == severities.SOFT]
        return {
            "totalEntries": total_entries,
            "hardCount": len(hard),
            "softCount": len(soft),
            "canPublish": not hard,
            "conflicts": [
                {
                    "id": c.id,
                    "conflictType": c.conflict_type,
                    "severity": c.severity,
                    "description": c.description,
                    "entry": c.entry_a_id,
                    "clashesWith": c.entry_b_id,
                }
                for c in conflicts
            ],
        }

    @action(detail=True, methods=["post"])
    def validate(self, request, pk=None):
        """Run conflict detection and return the report without publishing."""
        timetable = self.get_object()
        if timetable.status == models.Timetable.Status.PUBLISHED:
            return Response(
                {"success": False, "message": "This timetable is already published."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            conflicts = services.detect_conflicts(timetable, persist=True)
        except services.BusinessRuleError as exc:
            return _handle_rule_error(self, exc)
        report = self.conflict_report(conflicts, timetable.entries.count())
        return Response({"success": True, "data": report})

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        """Publish the draft (blocked while hard conflicts are unresolved)."""
        timetable = self.get_object()
        try:
            services.publish(timetable, request.user)
        except services.BusinessRuleError as exc:
            return _handle_rule_error(self, exc)
        data = self.read_serializer_class(
            timetable, context=self.get_serializer_context()
        ).data
        return Response({"success": True, "message": "Timetable published.", "data": data})

    @action(detail=True, methods=["get"])
    def entries(self, request, pk=None):
        """All (non-cancelled) entries of a timetable."""
        timetable = self.get_object()
        entries = (
            timetable.entries.select_related("period", "teacher", "subject")
            .exclude(status=models.TimetableEntry.Status.CANCELLED)
        )
        data = serializers.TimetableEntrySummarySerializer(entries, many=True).data
        return Response({"success": True, "data": data})

    @action(detail=True, methods=["get"])
    def grid(self, request, pk=None):
        """Weekly grid: each day maps to its period entries."""
        timetable = self.get_object()
        entries = (
            timetable.entries.select_related("period", "teacher", "subject")
            .exclude(status=models.TimetableEntry.Status.CANCELLED)
        )
        grid = {}
        for entry in entries:
            day = entry.get_day_display()
            grid.setdefault(day, []).append(
                serializers.TimetableEntrySummarySerializer(entry).data
            )
        return Response(
            {"success": True,
             "data": {"id": timetable.id, "version": timetable.version,
                      "status": timetable.status, "grid": grid}}
        )


class TimetableEntryViewSet(TenantModelViewSet):
    queryset = models.TimetableEntry.objects.all()
    serializer_class = serializers.TimetableEntrySerializer
    filterset_fields = ("timetable", "day", "period", "subject", "teacher", "status")
    search_fields = ("room",)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            instance = self.perform_create_and_validate(serializer, request)
        except IntegrityError as exc:
            return Response(
                {"success": False,
                 "message": "A duplicate day/period entry already exists.",
                 "errors": {"fieldErrors": {}, "formErrors": [str(exc)]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except services.BusinessRuleError as exc:
            return _handle_rule_error(self, exc)

        data = self.get_serializer(instance, context=self.get_serializer_context()).data
        return Response(
            {"success": True, "message": "Entry saved.", "data": data},
            status=status.HTTP_201_CREATED,
        )

    def perform_create_and_validate(self, serializer, request):
        from django.db import transaction as db_transaction

        with db_transaction.atomic():
            instance = serializer.save(institution_id=request.institution_id)
            # Drafts are allowed to hold conflicts; they only block publishing.
            services.detect_conflicts(instance.timetable, persist=True)
        return instance

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        if instance.timetable.status == models.Timetable.Status.PUBLISHED:
            return Response(
                {"success": False,
                 "message": ("Published timetables cannot be edited directly - "
                             "raise a change request."),
                 "errors": {"fieldErrors": {}, "formErrors": ["Published timetable entry."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {"success": True, "data": self.get_serializer(instance).data}
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.timetable.status == models.Timetable.Status.PUBLISHED:
            return Response(
                {"success": False,
                 "message": "Cancel published entries via a change request.",
                 "errors": {"fieldErrors": {}, "formErrors": ["Published timetable entry."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            services.cancel_entry(instance)
        except services.BusinessRuleError as exc:
            return _handle_rule_error(self, exc)
        return Response({"success": True, "message": "Entry cancelled."})


class TimetableChangeRequestViewSet(TenantModelViewSet):
    queryset = models.TimetableChangeRequest.objects.all()
    read_serializer_class = serializers.TimetableChangeRequestSerializer
    write_serializer_class = serializers.ChangeRequestWriteSerializer
    filterset_fields = ("status", "entry")
    search_fields = ("reason",)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return self.write_serializer_class
        return self.read_serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = serializer.validated_data.pop("entry")
        proposed_teacher = serializer.validated_data.pop("proposed_teacher", None)
        proposed_room = serializer.validated_data.pop("proposed_room", None)
        reason = serializer.validated_data.get("reason")

        try:
            change_request = services.create_change_request(
                entry, request.user, reason=reason,
                proposed_teacher=proposed_teacher, proposed_room=proposed_room,
            )
        except services.BusinessRuleError as exc:
            return _handle_rule_error(self, exc)

        data = self.read_serializer_class(
            change_request, context=self.get_serializer_context()
        ).data
        return Response({"success": True, "data": data}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        change_request = self.get_object()
        try:
            services.approve_change_request(change_request, request.user)
        except services.BusinessRuleError as exc:
            return _handle_rule_error(self, exc)
        data = self.read_serializer_class(
            change_request, context=self.get_serializer_context()
        ).data
        return Response({"success": True, "message": "Change approved.", "data": data})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        change_request = self.get_object()
        try:
            services.reject_change_request(
                change_request, request.user, request.data.get("reason", "")
            )
        except services.BusinessRuleError as exc:
            return _handle_rule_error(self, exc)
        data = self.read_serializer_class(
            change_request, context=self.get_serializer_context()
        ).data
        return Response({"success": True, "message": "Change rejected.", "data": data})
