from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0001_initial'),
        ('surveys', '0005_create_emailschedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailschedule',
            name='email_type',
            field=models.CharField(blank=True, choices=[('high_risk', 'High Risk Notification'), ('report', 'Member Reports'), ('summary', 'Organization Summary')], help_text='Type of bulk email to send', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='emailschedule',
            name='is_bulk',
            field=models.BooleanField(default=False, help_text='Whether this is a bulk email to multiple recipients'),
        ),
        migrations.AddField(
            model_name='emailschedule',
            name='organization',
            field=models.ForeignKey(blank=True, help_text='Organization for bulk emails', null=True, on_delete=models.deletion.CASCADE, related_name='email_schedules', to='groups.organization'),
        ),
        migrations.AlterField(
            model_name='emailschedule',
            name='frequency',
            field=models.CharField(choices=[('one_time', 'One Time'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('custom', 'Custom')], default='one_time', max_length=20),
        ),
        migrations.AlterField(
            model_name='emailschedule',
            name='recipient_email',
            field=models.EmailField(blank=True, help_text='Email address of the recipient (for single recipient)', max_length=254, null=True),
        ),
    ]
