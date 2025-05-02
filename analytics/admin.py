from django.contrib import admin
# Import directly from the module file, not from the package
from analytics.models.reports import Report
# Import from the main module file
from analytics.models import Dashboard, Widget

class WidgetInline(admin.TabularInline):
    model = Widget
    extra = 1

class DashboardAdmin(admin.ModelAdmin):
    list_display = ('title', 'layout', 'is_public', 'created_by', 'organization', 'created_at', 'get_widget_count')
    list_filter = ('layout', 'is_public', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [WidgetInline]

    def get_widget_count(self, obj):
        return obj.get_widget_count()
    get_widget_count.short_description = 'Widgets'

class WidgetAdmin(admin.ModelAdmin):
    list_display = ('title', 'dashboard', 'widget_type', 'data_source', 'position_x', 'position_y')
    list_filter = ('dashboard', 'widget_type', 'data_source')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')

class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_format', 'status', 'organization', 'created_by', 'created_at')
    list_filter = ('report_format', 'status', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(Dashboard, DashboardAdmin)
admin.site.register(Widget, WidgetAdmin)
admin.site.register(Report, ReportAdmin)
