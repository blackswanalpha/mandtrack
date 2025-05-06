from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    """
    This migration adds the questionnaire field to the Response model.
    """
    dependencies = [
        ('surveys', '0001_initial'),
        ('feedback', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='response',
            name='questionnaire',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questionnaire_responses', to='surveys.surveysquestionnaire'),
        ),
    ]
