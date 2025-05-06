from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('groups', '0001_initial'),
        ('feedback', '0004_merge_20250505_1156'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailSchedule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('email_type', models.CharField(choices=[('high_risk', 'High Risk Notification'), ('report', 'Member Reports'), ('summary', 'Organization Summary')], max_length=20)),
                ('frequency', models.CharField(choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly')], max_length=20)),
                ('day_of_week', models.IntegerField(blank=True, choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')], help_text='Required for weekly frequency', null=True)),
                ('day_of_month', models.IntegerField(blank=True, help_text='Day of month (1-31) for monthly frequency', null=True)),
                ('time_of_day', models.TimeField(help_text='Time of day to send the email (in UTC)')),
                ('is_active', models.BooleanField(default=True)),
                ('last_sent', models.DateTimeField(blank=True, null=True)),
                ('next_scheduled', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_email_schedules', to='auth.user')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_schedules', to='groups.organization')),
                ('questionnaire', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='email_schedules', to='surveys.questionnaire')),
                ('recipients', models.ManyToManyField(blank=True, help_text='Specific recipients (if empty, will use defaults based on email type)', related_name='email_schedules', to='auth.user')),
            ],
            options={
                'verbose_name': 'Email Schedule',
                'verbose_name_plural': 'Email Schedules',
                'ordering': ['next_scheduled'],
                'indexes': [
                    models.Index(fields=['organization'], name='fb_email_sched_org_idx'),
                    models.Index(fields=['email_type'], name='fb_email_sched_type_idx'),
                    models.Index(fields=['frequency'], name='fb_email_sched_freq_idx'),
                    models.Index(fields=['next_scheduled'], name='fb_email_sched_next_idx'),
                    models.Index(fields=['is_active'], name='fb_email_sched_active_idx'),
                ],
            },
        ),
    ]
