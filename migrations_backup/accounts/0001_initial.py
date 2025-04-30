from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdminProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('department', models.CharField(blank=True, max_length=100, null=True)),
                ('position', models.CharField(blank=True, max_length=100, null=True)),
                ('employee_id', models.CharField(blank=True, max_length=50, null=True)),
                ('admin_notes', models.TextField(blank=True)),
                ('access_level', models.CharField(choices=[('limited', 'Limited'), ('standard', 'Standard'), ('full', 'Full')], default='standard', max_length=20)),
                ('last_login_ip', models.GenericIPAddressField(blank=True, null=True)),
                ('preferences', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='admin_profile', to='users.user')),
            ],
            options={
                'verbose_name': 'Admin Profile',
                'verbose_name_plural': 'Admin Profiles',
            },
        ),
        migrations.CreateModel(
            name='AdminLoginHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('login_time', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('session_id', models.CharField(blank=True, max_length=100, null=True)),
                ('success', models.BooleanField(default=True)),
                ('failure_reason', models.CharField(blank=True, max_length=255, null=True)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='admin_login_history', to='users.user')),
            ],
            options={
                'verbose_name': 'Admin Login History',
                'verbose_name_plural': 'Admin Login Histories',
                'ordering': ['-login_time'],
            },
        ),
    ]
