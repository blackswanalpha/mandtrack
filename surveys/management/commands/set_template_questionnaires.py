from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Sets the is_template field for questionnaires that should be templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ids',
            type=str,
            help='Comma-separated list of questionnaire IDs to mark as templates',
        )
        parser.add_argument(
            '--titles',
            type=str,
            help='Comma-separated list of questionnaire titles to mark as templates',
        )
        parser.add_argument(
            '--all-with-prefix',
            type=str,
            help='Mark all questionnaires with titles starting with this prefix as templates',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        # Check if the is_template field exists
        try:
            with connection.cursor() as cursor:
                # SQLite-compatible way to check if column exists
                cursor.execute("PRAGMA table_info(surveys_questionnaire);")
                columns = cursor.fetchall()
                column_exists = any(col[1] == 'is_template' for col in columns)

                if not column_exists:
                    self.stdout.write(self.style.ERROR('The is_template field does not exist in the surveys_questionnaire table.'))
                    self.stdout.write(self.style.WARNING('Please run migrations first: python manage.py migrate'))
                    return
        except OperationalError as e:
            self.stdout.write(self.style.ERROR(f'Database error: {e}'))
            return

        # Process by IDs
        if options['ids']:
            ids = [id.strip() for id in options['ids'].split(',')]
            self._process_by_ids(ids, options['dry_run'])

        # Process by titles
        if options['titles']:
            titles = [title.strip() for title in options['titles'].split(',')]
            self._process_by_titles(titles, options['dry_run'])

        # Process by prefix
        if options['all_with_prefix']:
            prefix = options['all_with_prefix']
            self._process_by_prefix(prefix, options['dry_run'])

        # If no specific options provided, show help
        if not (options['ids'] or options['titles'] or options['all_with_prefix']):
            self.stdout.write(self.style.WARNING('No action specified. Please use --ids, --titles, or --all-with-prefix.'))
            self.stdout.write(self.style.WARNING('Example: python manage.py set_template_questionnaires --titles="Template 1,Template 2"'))

    def _process_by_ids(self, ids, dry_run):
        """Process questionnaires by IDs"""
        id_list = ', '.join([f"'{id}'" for id in ids])

        # First, get the questionnaires that will be affected
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT id, title FROM surveys_questionnaire WHERE id IN ({id_list});")
            questionnaires = cursor.fetchall()

            if not questionnaires:
                self.stdout.write(self.style.WARNING(f'No questionnaires found with the specified IDs.'))
                return

            self.stdout.write(self.style.SUCCESS(f'Found {len(questionnaires)} questionnaires:'))
            for q_id, title in questionnaires:
                self.stdout.write(f'  - {title} (ID: {q_id})')

            if dry_run:
                self.stdout.write(self.style.WARNING('DRY RUN: No changes made.'))
                return

            # Update the questionnaires
            cursor.execute(f"UPDATE surveys_questionnaire SET is_template = TRUE WHERE id IN ({id_list});")
            self.stdout.write(self.style.SUCCESS(f'Successfully marked {len(questionnaires)} questionnaires as templates.'))

    def _process_by_titles(self, titles, dry_run):
        """Process questionnaires by titles"""
        title_list = ', '.join([f"'{title}'" for title in titles])

        # First, get the questionnaires that will be affected
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT id, title FROM surveys_questionnaire WHERE title IN ({title_list});")
            questionnaires = cursor.fetchall()

            if not questionnaires:
                self.stdout.write(self.style.WARNING(f'No questionnaires found with the specified titles.'))
                return

            self.stdout.write(self.style.SUCCESS(f'Found {len(questionnaires)} questionnaires:'))
            for q_id, title in questionnaires:
                self.stdout.write(f'  - {title} (ID: {q_id})')

            if dry_run:
                self.stdout.write(self.style.WARNING('DRY RUN: No changes made.'))
                return

            # Update the questionnaires
            cursor.execute(f"UPDATE surveys_questionnaire SET is_template = TRUE WHERE title IN ({title_list});")
            self.stdout.write(self.style.SUCCESS(f'Successfully marked {len(questionnaires)} questionnaires as templates.'))

    def _process_by_prefix(self, prefix, dry_run):
        """Process questionnaires by title prefix"""
        # First, get the questionnaires that will be affected
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT id, title FROM surveys_questionnaire WHERE title LIKE '{prefix}%';")
            questionnaires = cursor.fetchall()

            if not questionnaires:
                self.stdout.write(self.style.WARNING(f'No questionnaires found with titles starting with "{prefix}".'))
                return

            self.stdout.write(self.style.SUCCESS(f'Found {len(questionnaires)} questionnaires:'))
            for q_id, title in questionnaires:
                self.stdout.write(f'  - {title} (ID: {q_id})')

            if dry_run:
                self.stdout.write(self.style.WARNING('DRY RUN: No changes made.'))
                return

            # Update the questionnaires
            cursor.execute(f"UPDATE surveys_questionnaire SET is_template = TRUE WHERE title LIKE '{prefix}%';")
            self.stdout.write(self.style.SUCCESS(f'Successfully marked {len(questionnaires)} questionnaires as templates.'))
