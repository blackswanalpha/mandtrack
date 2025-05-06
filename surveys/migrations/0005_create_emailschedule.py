from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
        ('surveys', '0004_alter_emaillog_sent_by_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject_override', models.CharField(blank=True, help_text='Override the template subject (optional)', max_length=255, null=True)),
                ('recipient_email', models.EmailField(max_length=254)),
                ('recipient_name', models.CharField(blank=True, help_text='Name of the recipient (optional)', max_length=255, null=True)),
                ('frequency', models.CharField(choices=[('one_time', 'One Time'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('custom', 'Custom')], default='one_time', max_length=20)),
                ('scheduled_time', models.DateTimeField(help_text='When to send the email')),
                ('end_date', models.DateTimeField(blank=True, help_text='End date for recurring emails (optional)', null=True)),
                ('custom_days', models.CharField(blank=True, help_text='JSON list of days for custom frequency (e.g., [0,3,6] for Sunday, Wednesday, Saturday)', max_length=100, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('last_sent', models.DateTimeField(blank=True, null=True)),
                ('next_send', models.DateTimeField(blank=True, null=True)),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('context_data', models.JSONField(blank=True, default=dict, help_text='JSON data for template variables')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_schedules', to=settings.AUTH_USER_MODEL)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='surveys.emailtemplate')),
            ],
            options={
                'verbose_name': 'Email Schedule',
                'verbose_name_plural': 'Email Schedules',
                'ordering': ['-scheduled_time'],
            },
        ),
    ]
