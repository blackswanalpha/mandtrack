from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Check the schema of the surveys_survey table'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'surveys_survey';")
            rows = cursor.fetchall()
            for row in rows:
                self.stdout.write(f"{row[0]} - {row[1]}")
