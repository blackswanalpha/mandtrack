from django.contrib import admin
from .models import Member, MemberAccess

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('member_number', 'name', 'email', 'organization', 'is_active', 'created_at')
    list_filter = ('is_active', 'organization', 'created_at')
    search_fields = ('member_number', 'name', 'email')
    ordering = ('member_number',)
    date_hierarchy = 'created_at'

@admin.register(MemberAccess)
class MemberAccessAdmin(admin.ModelAdmin):
    list_display = ('member', 'questionnaire', 'access_code', 'is_used', 'used_at', 'created_at')
    list_filter = ('is_used', 'questionnaire', 'created_at')
    search_fields = ('member__member_number', 'member__name', 'access_code', 'questionnaire__title')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
