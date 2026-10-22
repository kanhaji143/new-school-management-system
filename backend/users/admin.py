from django.contrib import admin

from . import models


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "institution", "is_active")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    @admin.display(description="Full name")
    def full_name(self, obj):
        return obj.full_name

@admin.register(models.Role)
class RoleAdmin(admin.ModelAdmin):
    pass

@admin.register(models.UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Invitation)
class InvitationAdmin(admin.ModelAdmin):
    pass