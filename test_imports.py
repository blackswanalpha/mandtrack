# Test imports
try:
    from surveys.models import Questionnaire, QuestionType, Question, QuestionChoice
    print("Successfully imported survey models")
    
    from feedback.models import Response, Answer
    print("Successfully imported feedback models")
    
    print("All imports successful!")
except Exception as e:
    print(f"Error: {e}")
