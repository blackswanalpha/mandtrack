from django.contrib import admin
from .models import AdminProfile, AdminLoginHistory

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'position', 'access_level', 'created_at')
    list_filter = ('access_level', 'created_at')
    search_fields = ('user__username', 'user__email', 'department', 'position', 'employee_id')
    readonly_fields = ('created_at', 'updated_at', 'last_login_ip')
    fieldsets = (
        (None, {'fields': ('user', 'department', 'position', 'employee_id')}),
        ('Access Information', {'fields': ('access_level', 'last_login_ip')}),
        ('Notes', {'fields': ('admin_notes',)}),
        ('Preferences', {'fields': ('preferences',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

@admin.register(AdminLoginHistory)
class AdminLoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'ip_address', 'success', 'failure_reason')
    list_filter = ('login_time', 'success')
    search_fields = ('user__username', 'user__email', 'ip_address', 'user_agent', 'session_id')
    readonly_fields = ('login_time', 'user', 'ip_address', 'user_agent', 'session_id', 'success', 'failure_reason')
    fieldsets = (
        (None, {'fields': ('user', 'login_time', 'success')}),
        ('Connection Information', {'fields': ('ip_address', 'user_agent', 'session_id')}),
        ('Failure Details', {'fields': ('failure_reason',)}),
    )
    ordering = ('-login_time',)
