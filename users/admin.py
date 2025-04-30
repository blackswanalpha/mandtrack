from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, ClientLoginHistory

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Client Profile'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('email', 'username', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'profile_image', 'phone_number')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Account Status', {'fields': ('email_verified', 'failed_login_attempts', 'account_locked_until', 'force_password_change')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'last_password_change')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role', 'is_staff', 'is_superuser'),
        }),
    )
    readonly_fields = ('date_joined', 'last_login', 'last_password_change')

@admin.register(ClientLoginHistory)
class ClientLoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'ip_address', 'success', 'failure_reason')
    list_filter = ('login_time', 'success')
    search_fields = ('user__username', 'user__email', 'ip_address', 'user_agent', 'session_id')
    readonly_fields = ('login_time', 'user', 'ip_address', 'user_agent', 'device_info', 'session_id', 'success', 'failure_reason')
    fieldsets = (
        (None, {'fields': ('user', 'login_time', 'success')}),
        ('Connection Information', {'fields': ('ip_address', 'user_agent', 'device_info', 'session_id')}),
        ('Failure Details', {'fields': ('failure_reason',)}),
    )
    ordering = ('-login_time',)

admin.site.register(User, UserAdmin)
