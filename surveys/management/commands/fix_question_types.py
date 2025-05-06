from django.core.management.base import BaseCommand
from django.db import connection, transaction
from surveys.models import QuestionType
from surveys.data.selector_data import QUESTION_TYPES
from surveys.models.question_type import get_icon_for_type

class Command(BaseCommand):
    help = 'Fix question types by ensuring all types are properly defined and have valid data'

    def handle(self, *args, **options):
        self.stdout.write("Starting question type fix...")

        # First, check if there are any records with empty code
        self.fix_empty_codes()

        # Then, ensure all question types from selector_data.py are present
        self.ensure_all_types_exist()

        # Finally, update all question types with proper icons and descriptions
        self.update_question_type_metadata()

        self.stdout.write(self.style.SUCCESS("Question types fixed successfully!"))

    def fix_empty_codes(self):
        """Fix any records with empty code values"""
        with connection.cursor() as cursor:
            # Check if there are any records with empty code
            cursor.execute("SELECT id, name FROM surveys_questiontype WHERE code = '' OR code IS NULL")
            empty_code_records = cursor.fetchall()

            if empty_code_records:
                self.stdout.write(f"Found {len(empty_code_records)} records with empty code")

                for record_id, name in empty_code_records:
                    # Try to determine the correct code based on the name
                    code = self.determine_code_from_name(name)

                    if code:
                        # Check if the code already exists
                        cursor.execute("SELECT id FROM surveys_questiontype WHERE code = %s", [code])
                        existing = cursor.fetchone()

                        if existing:
                            # Code already exists, so we need to delete this record
                            try:
                                cursor.execute("DELETE FROM surveys_questiontype WHERE id = %s", [record_id])
                                self.stdout.write(self.style.WARNING(
                                    f"Deleted record {record_id} with name '{name}' (code '{code}' already exists)"
                                ))
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f"Error deleting record {record_id}: {e}"))
                        else:
                            # Update the record with the determined code
                            try:
                                cursor.execute(
                                    "UPDATE surveys_questiontype SET code = %s WHERE id = %s",
                                    [code, record_id]
                                )
                                self.stdout.write(self.style.SUCCESS(f"Fixed record {record_id}: '{name}' → code='{code}'"))
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f"Error updating record {record_id}: {e}"))
                    else:
                        # If we can't determine the code, delete the record
                        try:
                            cursor.execute("DELETE FROM surveys_questiontype WHERE id = %s", [record_id])
                            self.stdout.write(self.style.WARNING(f"Deleted record {record_id} with name '{name}' (couldn't determine code)"))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Error deleting record {record_id}: {e}"))
            else:
                self.stdout.write("No records with empty code found")

    def determine_code_from_name(self, name):
        """Try to determine the code based on the name"""
        if not name:
            return None

        # Normalize the name
        normalized_name = name.lower().strip()

        # Check if the name matches any known type
        for code, type_name in QUESTION_TYPES:
            if normalized_name == type_name.lower():
                return code

        # Special case for "Multiple Choice" which might be the first record
        if normalized_name == "multiple choice":
            return "multiple_choice"

        # If we can't determine the code, return None
        return None

    @transaction.atomic
    def ensure_all_types_exist(self):
        """Ensure all question types from selector_data.py exist in the database"""
        # Get existing types
        existing_types = {qt.code: qt for qt in QuestionType.objects.all()}

        # Get default types
        default_types = QuestionType.get_default_types()

        created_count = 0

        # Create any missing types
        for type_data in default_types:
            code = type_data['code']
            if code not in existing_types:
                QuestionType.objects.create(**type_data)
                created_count += 1
                self.stdout.write(f"Created missing question type: {type_data['name']} ({code})")

        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f"Created {created_count} missing question types"))
        else:
            self.stdout.write("All question types already exist")

    @transaction.atomic
    def update_question_type_metadata(self):
        """Update all question types with proper icons and descriptions"""
        updated_count = 0

        for question_type in QuestionType.objects.all():
            needs_update = False

            # Skip records with empty code (they should be fixed by fix_empty_codes)
            if not question_type.code:
                self.stdout.write(self.style.WARNING(f"Skipping record with empty code: {question_type.id} - {question_type.name}"))
                continue

            # Update icon if empty or default
            if not question_type.icon or question_type.icon == 'fa-question':
                question_type.icon = get_icon_for_type(question_type.code)
                needs_update = True

            # Update description if empty
            if not question_type.description:
                question_type.description = f"{question_type.name} question type"
                needs_update = True

            if needs_update:
                question_type.save()
                updated_count += 1
                self.stdout.write(f"Updated metadata for question type: {question_type.name} ({question_type.code})")

        if updated_count > 0:
            self.stdout.write(self.style.SUCCESS(f"Updated metadata for {updated_count} question types"))
        else:
            self.stdout.write("All question types have proper metadata")
