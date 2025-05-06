# Generated manually

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('feedback', '0006_merge_0005_delete_emailschedule_0005_emailschedule'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email_type', models.CharField(choices=[('high_risk', 'High Risk Notification'), ('report', 'Response Report'), ('bulk', 'Bulk Notification'), ('other', 'Other')], max_length=20)),
                ('subject', models.CharField(max_length=255)),
                ('recipient_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('sender_email', models.EmailField(default=settings.DEFAULT_FROM_EMAIL, max_length=254)),
                ('template', models.CharField(blank=True, max_length=255, null=True)),
                ('context', models.JSONField(default=dict)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='email_logs', to='groups.organization')),
                ('response', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='email_logs', to='feedback.response')),
                ('sent_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_emails', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Email Log',
                'verbose_name_plural': 'Email Logs',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['email_type'], name='fb_email_type_idx1'),
                    models.Index(fields=['status'], name='fb_email_status_idx1'),
                    models.Index(fields=['recipient_email'], name='fb_email_recipient_idx1'),
                    models.Index(fields=['response'], name='fb_email_response_idx1'),
                    models.Index(fields=['organization'], name='fb_email_org_idx1'),
                    models.Index(fields=['created_at'], name='fb_email_created_at_idx1'),
                ],
            },
        ),
    ]
