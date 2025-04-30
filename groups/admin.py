from django.contrib import admin
from .models import Organization, OrganizationMember

class OrganizationMemberInline(admin.TabularInline):
    model = OrganizationMember
    extra = 1

class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'created_by', 'created_at', 'get_member_count')
    list_filter = ('type', 'created_at')
    search_fields = ('name', 'description', 'email')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    inlines = [OrganizationMemberInline]

    def get_member_count(self, obj):
        return obj.get_member_count()
    get_member_count.short_description = 'Members'

class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role', 'is_active', 'joined_at')
    list_filter = ('organization', 'role', 'is_active', 'joined_at')
    search_fields = ('user__username', 'user__email', 'title', 'department')
    readonly_fields = ('joined_at', 'updated_at')

admin.site.register(Organization, OrganizationAdmin)
admin.site.register(OrganizationMember, OrganizationMemberAdmin)
