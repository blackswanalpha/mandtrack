from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0001_initial'),  # Adjust this to the latest migration in your surveys app
    ]

    operations = [
        migrations.AddField(
            model_name='surveysquestion',
            name='question_type_obj',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='questions', to='surveys.questiontype'),
        ),
    ]
