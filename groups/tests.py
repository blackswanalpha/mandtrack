from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from .models import Organization, OrganizationMember

User = get_user_model()

class OrganizationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        self.organization = Organization.objects.create(
            name='Test Organization',
            description='This is a test organization',
            type='healthcare',
            website='https://example.com',
            email='org@example.com',
            phone='123-456-7890',
            address='123 Test St, Test City, TS 12345',
            created_by=self.user
        )

    def test_organization_creation(self):
        """Test that an organization can be created"""
        self.assertEqual(self.organization.name, 'Test Organization')
        self.assertEqual(self.organization.description, 'This is a test organization')
        self.assertEqual(self.organization.type, 'healthcare')
        self.assertEqual(self.organization.website, 'https://example.com')
        self.assertEqual(self.organization.email, 'org@example.com')
        self.assertEqual(self.organization.phone, '123-456-7890')
        self.assertEqual(self.organization.address, '123 Test St, Test City, TS 12345')
        self.assertEqual(self.organization.created_by, self.user)

    def test_organization_slug_generation(self):
        """Test that a slug is automatically generated"""
        self.assertEqual(self.organization.slug, slugify(self.organization.name))

    def test_organization_string_representation(self):
        """Test the string representation of an organization"""
        self.assertEqual(str(self.organization), 'Test Organization')

    def test_get_member_count(self):
        """Test the get_member_count method"""
        # Initially only the creator is a member
        self.assertEqual(self.organization.get_member_count(), 1)

        # Create another user and add as member
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpassword'
        )

        OrganizationMember.objects.create(
            organization=self.organization,
            user=user2,
            role='member'
        )

        # Now should have 2 members
        self.assertEqual(self.organization.get_member_count(), 2)

    def test_get_absolute_url(self):
        """Test the get_absolute_url method"""
        self.assertEqual(self.organization.get_absolute_url(), f"/organizations/{self.organization.slug}/")


class OrganizationMemberModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='testpassword'
        )

        self.organization = Organization.objects.create(
            name='Test Organization',
            type='healthcare',
            created_by=self.admin_user
        )

        # The admin user is automatically added as a member with admin role

        # Add the regular user as a member
        self.member = OrganizationMember.objects.create(
            organization=self.organization,
            user=self.user,
            role='member',
            title='Test Title',
            department='Test Department'
        )

    def test_member_creation(self):
        """Test that an organization member can be created"""
        self.assertEqual(self.member.organization, self.organization)
        self.assertEqual(self.member.user, self.user)
        self.assertEqual(self.member.role, 'member')
        self.assertEqual(self.member.title, 'Test Title')
        self.assertEqual(self.member.department, 'Test Department')
        self.assertTrue(self.member.is_active)

    def test_admin_member_creation(self):
        """Test that the creator is added as an admin member"""
        admin_member = OrganizationMember.objects.get(organization=self.organization, user=self.admin_user)
        self.assertEqual(admin_member.role, 'admin')

    def test_member_string_representation(self):
        """Test the string representation of an organization member"""
        self.assertEqual(str(self.member), f"{self.user.username} - {self.organization.name}")

    def test_get_role_display(self):
        """Test the get_role_display method"""
        self.assertEqual(self.member.get_role_display(), 'Member')
