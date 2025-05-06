# Questionnaire ORM Selector

This document explains the implementation of the questionnaire ORM selector in the surveys app.

## Overview

The questionnaire ORM selector provides a way to ensure that the Questionnaire model has the proper choices for category, type, and status fields. This is important for maintaining data integrity and providing a consistent user experience.

## Files

- `surveys/models/mixins.py`: Contains the `QuestionnaireSelectorMixin` that adds selector fields to the Questionnaire model
- `surveys/apps.py`: Updated to apply the mixin to the Questionnaire model
- `surveys/management/commands/fix_questionnaire_orm_selector.py`: Management command to fix the questionnaire ORM selector
- `surveys/management/commands/initialize_question_types.py`: Management command to initialize question types
- `surveys/data/selector_data.py`: Contains the data for the selector fields

## How It Works

1. The `QuestionnaireSelectorMixin` adds the proper choices to the Questionnaire model fields
2. The app configuration applies the mixin to the Questionnaire model when the app is loaded
3. The `fix_questionnaire_orm_selector` command updates any invalid values in the database
4. The `initialize_question_types` command initializes the question types

## Usage

To fix the questionnaire ORM selector, run:

```bash
python manage.py fix_questionnaire_orm_selector
```

To initialize question types, run:

```bash
python manage.py initialize_question_types
```

## Data Definitions

The selector data is defined in `surveys/data/selector_data.py`:

- `QUESTIONNAIRE_CATEGORIES`: List of tuples with category code and name
- `QUESTIONNAIRE_TYPES`: List of tuples with type code and name
- `QUESTIONNAIRE_STATUSES`: List of tuples with status code and name
- `QUESTION_TYPES`: List of tuples with question type code and name
- `QUESTION_CATEGORIES`: List of tuples with question category code and name

## Database Constraints

For PostgreSQL databases, the command adds check constraints to ensure that the values in the database match the allowed values. For SQLite databases, the constraints are enforced by the Django ORM.

## Troubleshooting

If you encounter issues with the questionnaire ORM selector, try the following:

1. Run the `fix_questionnaire_orm_selector` command to update any invalid values
2. Check the database schema to ensure the fields have the proper constraints
3. Verify that the selector data in `surveys/data/selector_data.py` is correct
4. Check the app configuration to ensure the mixin is applied correctly

## Adding New Selector Values

To add new selector values:

1. Update the appropriate list in `surveys/data/selector_data.py`
2. Run the `fix_questionnaire_orm_selector` command to update the database

## Model Relationships

The Questionnaire model has relationships with other models in the app:

- `questions`: One-to-many relationship with Question model
- `qr_codes`: One-to-many relationship with QRCode model
- `organization`: Many-to-one relationship with Organization model
- `created_by`: Many-to-one relationship with User model

These relationships are maintained when updating the selector fields.
