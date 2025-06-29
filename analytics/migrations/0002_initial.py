# Generated by Django 5.2 on 2025-05-06 20:00

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('analytics', '0001_initial'),
        ('feedback', '0001_initial'),
        ('groups', '0001_initial'),
        ('surveys', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='aianalysisconfiguration',
            name='questionnaire',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_configurations', to='surveys.surveysquestionnaire'),
        ),
        migrations.AddField(
            model_name='aianalysisresult',
            name='analyzed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='conducted_analyses', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='aianalysisresult',
            name='configuration',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='analysis_results', to='analytics.aianalysisconfiguration'),
        ),
        migrations.AddField(
            model_name='aianalysisresult',
            name='response',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_analyses', to='feedback.response'),
        ),
        migrations.AddField(
            model_name='aifeedback',
            name='analysis_result',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedback', to='analytics.aianalysisresult'),
        ),
        migrations.AddField(
            model_name='aifeedback',
            name='provided_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ai_feedback', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='aiinsight',
            name='questionnaire',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_insights', to='surveys.surveysquestionnaire'),
        ),
        migrations.AddField(
            model_name='aiinsight',
            name='related_responses',
            field=models.ManyToManyField(blank=True, related_name='insights', to='feedback.response'),
        ),
        migrations.AddField(
            model_name='aimodel',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_ai_models', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='aiinsight',
            name='ai_model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='generated_insights', to='analytics.aimodel'),
        ),
        migrations.AddField(
            model_name='aianalysisresult',
            name='ai_model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analysis_results', to='analytics.aimodel'),
        ),
        migrations.AddField(
            model_name='aianalysisconfiguration',
            name='ai_model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questionnaire_configurations', to='analytics.aimodel'),
        ),
        migrations.AddField(
            model_name='batchanalysisjob',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_batch_jobs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='batchanalysisjob',
            name='responses',
            field=models.ManyToManyField(related_name='batch_jobs', to='feedback.response'),
        ),
        migrations.AddField(
            model_name='dashboard',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dashboards', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='dashboard',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dashboards', to='groups.organization'),
        ),
        migrations.AddField(
            model_name='report',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_reports', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='report',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reports', to='groups.organization'),
        ),
        migrations.AddField(
            model_name='report',
            name='questionnaire',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reports', to='surveys.surveysquestionnaire'),
        ),
        migrations.AddField(
            model_name='reportschedule',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_report_schedules', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='reportschedule',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='report_schedules', to='groups.organization'),
        ),
        migrations.AddField(
            model_name='reportschedule',
            name='questionnaire',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='report_schedules', to='surveys.surveysquestionnaire'),
        ),
        migrations.AddField(
            model_name='scheduledreport',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_reports', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='widget',
            name='dashboard',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='widgets', to='analytics.dashboard'),
        ),
        migrations.AlterUniqueTogether(
            name='aianalysisconfiguration',
            unique_together={('questionnaire', 'ai_model')},
        ),
    ]
