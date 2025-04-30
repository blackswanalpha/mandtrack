from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Dashboard, Widget, Report
from surveys.models import Survey
from groups.models import Organization

User = get_user_model()

class DashboardModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        self.organization = Organization.objects.create(
            name='Test Organization',
            type='healthcare',
            created_by=self.user
        )

        self.dashboard = Dashboard.objects.create(
            title='Test Dashboard',
            description='This is a test dashboard',
            layout='grid',
            created_by=self.user,
            organization=self.organization,
            is_public=False
        )

    def test_dashboard_creation(self):
        """Test that a dashboard can be created"""
        self.assertEqual(self.dashboard.title, 'Test Dashboard')
        self.assertEqual(self.dashboard.description, 'This is a test dashboard')
        self.assertEqual(self.dashboard.layout, 'grid')
        self.assertEqual(self.dashboard.created_by, self.user)
        self.assertEqual(self.dashboard.organization, self.organization)
        self.assertFalse(self.dashboard.is_public)

    def test_dashboard_string_representation(self):
        """Test the string representation of a dashboard"""
        self.assertEqual(str(self.dashboard), 'Test Dashboard')

    def test_get_widget_count(self):
        """Test the get_widget_count method"""
        # Initially no widgets
        self.assertEqual(self.dashboard.get_widget_count(), 0)

        # Add a widget
        Widget.objects.create(
            dashboard=self.dashboard,
            title='Test Widget',
            widget_type='chart_bar',
            data_source='survey',
            width=4,
            height=4,
            position_x=0,
            position_y=0
        )

        # Now should have 1 widget
        self.assertEqual(self.dashboard.get_widget_count(), 1)


class WidgetModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        self.dashboard = Dashboard.objects.create(
            title='Test Dashboard',
            layout='grid',
            created_by=self.user
        )

        self.widget = Widget.objects.create(
            dashboard=self.dashboard,
            title='Test Widget',
            description='This is a test widget',
            widget_type='chart_bar',
            data_source='survey',
            width=4,
            height=4,
            position_x=0,
            position_y=0,
            config={'test_key': 'test_value'}
        )

    def test_widget_creation(self):
        """Test that a widget can be created"""
        self.assertEqual(self.widget.dashboard, self.dashboard)
        self.assertEqual(self.widget.title, 'Test Widget')
        self.assertEqual(self.widget.description, 'This is a test widget')
        self.assertEqual(self.widget.widget_type, 'chart_bar')
        self.assertEqual(self.widget.data_source, 'survey')
        self.assertEqual(self.widget.width, 4)
        self.assertEqual(self.widget.height, 4)
        self.assertEqual(self.widget.position_x, 0)
        self.assertEqual(self.widget.position_y, 0)
        self.assertEqual(self.widget.config, {'test_key': 'test_value'})

    def test_widget_string_representation(self):
        """Test the string representation of a widget"""
        self.assertEqual(str(self.widget), 'Test Widget')


class ReportModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        self.organization = Organization.objects.create(
            name='Test Organization',
            type='healthcare',
            created_by=self.user
        )

        self.survey = Survey.objects.create(
            title='Test Survey',
            category='anxiety',
            status='active',
            created_by=self.user,
            organization=self.organization
        )

        self.report = Report.objects.create(
            title='Test Report',
            description='This is a test report',
            report_format='pdf',
            created_by=self.user,
            organization=self.organization,
            status='pending'
        )
        self.report.surveys.add(self.survey)

    def test_report_creation(self):
        """Test that a report can be created"""
        self.assertEqual(self.report.title, 'Test Report')
        self.assertEqual(self.report.description, 'This is a test report')
        self.assertEqual(self.report.report_format, 'pdf')
        self.assertEqual(self.report.created_by, self.user)
        self.assertEqual(self.report.organization, self.organization)
        self.assertEqual(self.report.status, 'pending')
        self.assertEqual(self.report.surveys.count(), 1)
        self.assertIn(self.survey, self.report.surveys.all())

    def test_report_string_representation(self):
        """Test the string representation of a report"""
        self.assertEqual(str(self.report), 'Test Report')

    def test_get_survey_count(self):
        """Test the get_survey_count method"""
        self.assertEqual(self.report.get_survey_count(), 1)

        # Add another survey
        survey2 = Survey.objects.create(
            title='Test Survey 2',
            category='depression',
            status='active',
            created_by=self.user,
            organization=self.organization
        )
        self.report.surveys.add(survey2)

        # Now should have 2 surveys
        self.assertEqual(self.report.get_survey_count(), 2)
