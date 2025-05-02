"""
Script to generate realistic data for questionnaires, questions, responses, answers, scoring, and AI analysis.
"""
import os
import django
import sys
import random
from datetime import datetime, timedelta
import uuid
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

# Import models after Django setup
from django.contrib.auth import get_user_model
from django.utils import timezone
from surveys.models import Questionnaire, Question, QuestionChoice, QRCode, ScoringConfig
from feedback.models import Response, Answer, AIAnalysis
from groups.models import Organization, OrganizationMember
from analytics.models import AIModel, AIAnalysisResult, AIInsight

User = get_user_model()

# Sample data for questionnaires
QUESTIONNAIRE_DATA = [
    {
        "title": "Depression Assessment Questionnaire",
        "description": "A comprehensive assessment tool for evaluating depression symptoms and severity.",
        "category": "depression",
        "estimated_time": 15,
        "questions": [
            {
                "text": "Over the past 2 weeks, how often have you felt little interest or pleasure in doing things?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            },
            {
                "text": "Over the past 2 weeks, how often have you felt down, depressed, or hopeless?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            },
            {
                "text": "Over the past 2 weeks, how often have you had trouble falling or staying asleep, or sleeping too much?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            },
            {
                "text": "Over the past 2 weeks, how often have you felt tired or had little energy?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            },
            {
                "text": "Over the past 2 weeks, how often have you had poor appetite or overeating?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            },
            {
                "text": "Over the past 2 weeks, how often have you felt bad about yourself — or that you are a failure or have let yourself or your family down?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            },
            {
                "text": "Over the past 2 weeks, how often have you had trouble concentrating on things, such as reading the newspaper or watching television?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            },
            {
                "text": "Over the past 2 weeks, how often have you been moving or speaking so slowly that other people could have noticed? Or so fidgety or restless that you have been moving a lot more than usual?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            },
            {
                "text": "Over the past 2 weeks, how often have you had thoughts that you would be better off dead, or thoughts of hurting yourself in some way?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            }
        ],
        "scoring": {
            "name": "PHQ-9 Depression Severity",
            "description": "Standard scoring for the PHQ-9 depression assessment",
            "scoring_method": "sum",
            "max_score": 27,
            "passing_score": 5,
            "rules": [
                {"min": 0, "max": 4, "label": "Minimal", "color": "#00FF00", "description": "Minimal or no depression"},
                {"min": 5, "max": 9, "label": "Mild", "color": "#FFFF00", "description": "Mild depression"},
                {"min": 10, "max": 14, "label": "Moderate", "color": "#FFA500", "description": "Moderate depression"},
                {"min": 15, "max": 19, "label": "Moderately Severe", "color": "#FF4500", "description": "Moderately severe depression"},
                {"min": 20, "max": 27, "label": "Severe", "color": "#FF0000", "description": "Severe depression"}
            ]
        }
    },
    {
        "title": "Anxiety Assessment Questionnaire",
        "description": "A tool for evaluating anxiety symptoms and severity.",
        "category": "anxiety",
        "estimated_time": 10,
        "questions": [
            {
                "text": "Over the last 2 weeks, how often have you been bothered by feeling nervous, anxious, or on edge?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            },
            {
                "text": "Over the last 2 weeks, how often have you been bothered by not being able to stop or control worrying?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            },
            {
                "text": "Over the last 2 weeks, how often have you been bothered by worrying too much about different things?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            },
            {
                "text": "Over the last 2 weeks, how often have you been bothered by trouble relaxing?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            },
            {
                "text": "Over the last 2 weeks, how often have you been bothered by being so restless that it's hard to sit still?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            },
            {
                "text": "Over the last 2 weeks, how often have you been bothered by becoming easily annoyed or irritable?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            },
            {
                "text": "Over the last 2 weeks, how often have you been bothered by feeling afraid as if something awful might happen?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "Several days", "score": 1},
                    {"text": "More than half the days", "score": 2},
                    {"text": "Nearly every day", "score": 3}
                ]
            }
        ],
        "scoring": {
            "name": "GAD-7 Anxiety Severity",
            "description": "Standard scoring for the GAD-7 anxiety assessment",
            "scoring_method": "sum",
            "max_score": 21,
            "passing_score": 5,
            "rules": [
                {"min": 0, "max": 4, "label": "Minimal", "color": "#00FF00", "description": "Minimal anxiety"},
                {"min": 5, "max": 9, "label": "Mild", "color": "#FFFF00", "description": "Mild anxiety"},
                {"min": 10, "max": 14, "label": "Moderate", "color": "#FFA500", "description": "Moderate anxiety"},
                {"min": 15, "max": 21, "label": "Severe", "color": "#FF0000", "description": "Severe anxiety"}
            ]
        }
    },
    {
        "title": "Stress Assessment Questionnaire",
        "description": "A tool for evaluating stress levels and coping mechanisms.",
        "category": "stress",
        "estimated_time": 12,
        "questions": [
            {
                "text": "In the last month, how often have you been upset because of something that happened unexpectedly?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 0},
                    {"text": "Almost Never", "score": 1},
                    {"text": "Sometimes", "score": 2},
                    {"text": "Fairly Often", "score": 3},
                    {"text": "Very Often", "score": 4}
                ]
            },
            {
                "text": "In the last month, how often have you felt that you were unable to control the important things in your life?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 0},
                    {"text": "Almost Never", "score": 1},
                    {"text": "Sometimes", "score": 2},
                    {"text": "Fairly Often", "score": 3},
                    {"text": "Very Often", "score": 4}
                ]
            },
            {
                "text": "In the last month, how often have you felt nervous and stressed?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 0},
                    {"text": "Almost Never", "score": 1},
                    {"text": "Sometimes", "score": 2},
                    {"text": "Fairly Often", "score": 3},
                    {"text": "Very Often", "score": 4}
                ]
            },
            {
                "text": "In the last month, how often have you felt confident about your ability to handle your personal problems?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 4},
                    {"text": "Almost Never", "score": 3},
                    {"text": "Sometimes", "score": 2},
                    {"text": "Fairly Often", "score": 1},
                    {"text": "Very Often", "score": 0}
                ]
            },
            {
                "text": "In the last month, how often have you felt that things were going your way?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 4},
                    {"text": "Almost Never", "score": 3},
                    {"text": "Sometimes", "score": 2},
                    {"text": "Fairly Often", "score": 1},
                    {"text": "Very Often", "score": 0}
                ]
            },
            {
                "text": "In the last month, how often have you found that you could not cope with all the things that you had to do?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 0},
                    {"text": "Almost Never", "score": 1},
                    {"text": "Sometimes", "score": 2},
                    {"text": "Fairly Often", "score": 3},
                    {"text": "Very Often", "score": 4}
                ]
            },
            {
                "text": "In the last month, how often have you been able to control irritations in your life?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 4},
                    {"text": "Almost Never", "score": 3},
                    {"text": "Sometimes", "score": 2},
                    {"text": "Fairly Often", "score": 1},
                    {"text": "Very Often", "score": 0}
                ]
            },
            {
                "text": "In the last month, how often have you felt that you were on top of things?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 4},
                    {"text": "Almost Never", "score": 3},
                    {"text": "Sometimes", "score": 2},
                    {"text": "Fairly Often", "score": 1},
                    {"text": "Very Often", "score": 0}
                ]
            },
            {
                "text": "In the last month, how often have you been angered because of things that happened that were outside of your control?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 0},
                    {"text": "Almost Never", "score": 1},
                    {"text": "Sometimes", "score": 2},
                    {"text": "Fairly Often", "score": 3},
                    {"text": "Very Often", "score": 4}
                ]
            },
            {
                "text": "In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 0},
                    {"text": "Almost Never", "score": 1},
                    {"text": "Sometimes", "score": 2},
                    {"text": "Fairly Often", "score": 3},
                    {"text": "Very Often", "score": 4}
                ]
            }
        ],
        "scoring": {
            "name": "PSS-10 Stress Scale",
            "description": "Perceived Stress Scale scoring",
            "scoring_method": "sum",
            "max_score": 40,
            "passing_score": 13,
            "rules": [
                {"min": 0, "max": 13, "label": "Low", "color": "#00FF00", "description": "Low stress"},
                {"min": 14, "max": 26, "label": "Moderate", "color": "#FFFF00", "description": "Moderate stress"},
                {"min": 27, "max": 40, "label": "High", "color": "#FF0000", "description": "High perceived stress"}
            ]
        }
    },
    {
        "title": "PTSD Screening Questionnaire",
        "description": "A screening tool for post-traumatic stress disorder symptoms.",
        "category": "ptsd",
        "estimated_time": 10,
        "questions": [
            {
                "text": "In the past month, have you had nightmares about the event(s) or thought about the event(s) when you did not want to?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "No", "score": 0},
                    {"text": "Yes", "score": 1}
                ]
            },
            {
                "text": "In the past month, have you tried hard not to think about the event(s) or went out of your way to avoid situations that reminded you of the event(s)?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "No", "score": 0},
                    {"text": "Yes", "score": 1}
                ]
            },
            {
                "text": "In the past month, have you been constantly on guard, watchful, or easily startled?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "No", "score": 0},
                    {"text": "Yes", "score": 1}
                ]
            },
            {
                "text": "In the past month, have you felt numb or detached from people, activities, or your surroundings?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "No", "score": 0},
                    {"text": "Yes", "score": 1}
                ]
            },
            {
                "text": "In the past month, have you felt guilty or unable to stop blaming yourself or others for the event(s) or any problems the event(s) may have caused?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "No", "score": 0},
                    {"text": "Yes", "score": 1}
                ]
            }
        ],
        "scoring": {
            "name": "PC-PTSD-5 Screening",
            "description": "Primary Care PTSD Screen for DSM-5",
            "scoring_method": "sum",
            "max_score": 5,
            "passing_score": 3,
            "rules": [
                {"min": 0, "max": 2, "label": "Low", "color": "#00FF00", "description": "Low probability of PTSD"},
                {"min": 3, "max": 5, "label": "High", "color": "#FF0000", "description": "High probability of PTSD, further assessment recommended"}
            ]
        }
    },
    {
        "title": "Insomnia Severity Assessment",
        "description": "A tool for evaluating insomnia symptoms and their impact.",
        "category": "sleep",
        "estimated_time": 8,
        "questions": [
            {
                "text": "Please rate the severity of your insomnia problem(s): Difficulty falling asleep",
                "question_type": "single_choice",
                "choices": [
                    {"text": "None", "score": 0},
                    {"text": "Mild", "score": 1},
                    {"text": "Moderate", "score": 2},
                    {"text": "Severe", "score": 3},
                    {"text": "Very Severe", "score": 4}
                ]
            },
            {
                "text": "Please rate the severity of your insomnia problem(s): Difficulty staying asleep",
                "question_type": "single_choice",
                "choices": [
                    {"text": "None", "score": 0},
                    {"text": "Mild", "score": 1},
                    {"text": "Moderate", "score": 2},
                    {"text": "Severe", "score": 3},
                    {"text": "Very Severe", "score": 4}
                ]
            },
            {
                "text": "Please rate the severity of your insomnia problem(s): Problems waking up too early",
                "question_type": "single_choice",
                "choices": [
                    {"text": "None", "score": 0},
                    {"text": "Mild", "score": 1},
                    {"text": "Moderate", "score": 2},
                    {"text": "Severe", "score": 3},
                    {"text": "Very Severe", "score": 4}
                ]
            },
            {
                "text": "How satisfied/dissatisfied are you with your current sleep pattern?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Very Satisfied", "score": 0},
                    {"text": "Satisfied", "score": 1},
                    {"text": "Neutral", "score": 2},
                    {"text": "Dissatisfied", "score": 3},
                    {"text": "Very Dissatisfied", "score": 4}
                ]
            },
            {
                "text": "How noticeable to others do you think your sleep problem is in terms of impairing the quality of your life?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all Noticeable", "score": 0},
                    {"text": "A Little", "score": 1},
                    {"text": "Somewhat", "score": 2},
                    {"text": "Much", "score": 3},
                    {"text": "Very Much Noticeable", "score": 4}
                ]
            },
            {
                "text": "How worried/distressed are you about your current sleep problem?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "A Little", "score": 1},
                    {"text": "Somewhat", "score": 2},
                    {"text": "Much", "score": 3},
                    {"text": "Very Much", "score": 4}
                ]
            },
            {
                "text": "To what extent do you consider your sleep problem to interfere with your daily functioning (e.g., daytime fatigue, mood, ability to function at work/daily chores, concentration, memory, etc.)?",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all Interfering", "score": 0},
                    {"text": "A Little", "score": 1},
                    {"text": "Somewhat", "score": 2},
                    {"text": "Much", "score": 3},
                    {"text": "Very Much Interfering", "score": 4}
                ]
            }
        ],
        "scoring": {
            "name": "Insomnia Severity Index (ISI)",
            "description": "Standard scoring for the Insomnia Severity Index",
            "scoring_method": "sum",
            "max_score": 28,
            "passing_score": 8,
            "rules": [
                {"min": 0, "max": 7, "label": "No Insomnia", "color": "#00FF00", "description": "No clinically significant insomnia"},
                {"min": 8, "max": 14, "label": "Subthreshold", "color": "#FFFF00", "description": "Subthreshold insomnia"},
                {"min": 15, "max": 21, "label": "Moderate", "color": "#FFA500", "description": "Clinical insomnia (moderate severity)"},
                {"min": 22, "max": 28, "label": "Severe", "color": "#FF0000", "description": "Clinical insomnia (severe)"}
            ]
        }
    },
    {
        "title": "Social Anxiety Assessment",
        "description": "A tool for evaluating symptoms of social anxiety disorder.",
        "category": "anxiety",
        "estimated_time": 12,
        "questions": [
            {
                "text": "I feel uncomfortable at parties and other social events.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "A little bit", "score": 1},
                    {"text": "Somewhat", "score": 2},
                    {"text": "Very much", "score": 3},
                    {"text": "Extremely", "score": 4}
                ]
            },
            {
                "text": "I worry about embarrassing myself in social situations.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "A little bit", "score": 1},
                    {"text": "Somewhat", "score": 2},
                    {"text": "Very much", "score": 3},
                    {"text": "Extremely", "score": 4}
                ]
            },
            {
                "text": "I avoid talking to people I don't know.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "A little bit", "score": 1},
                    {"text": "Somewhat", "score": 2},
                    {"text": "Very much", "score": 3},
                    {"text": "Extremely", "score": 4}
                ]
            },
            {
                "text": "I fear that others will judge me negatively.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "A little bit", "score": 1},
                    {"text": "Somewhat", "score": 2},
                    {"text": "Very much", "score": 3},
                    {"text": "Extremely", "score": 4}
                ]
            },
            {
                "text": "I feel self-conscious around others.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "A little bit", "score": 1},
                    {"text": "Somewhat", "score": 2},
                    {"text": "Very much", "score": 3},
                    {"text": "Extremely", "score": 4}
                ]
            },
            {
                "text": "I avoid activities in which I am the center of attention.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "A little bit", "score": 1},
                    {"text": "Somewhat", "score": 2},
                    {"text": "Very much", "score": 3},
                    {"text": "Extremely", "score": 4}
                ]
            },
            {
                "text": "I get anxious when meeting new people.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "A little bit", "score": 1},
                    {"text": "Somewhat", "score": 2},
                    {"text": "Very much", "score": 3},
                    {"text": "Extremely", "score": 4}
                ]
            },
            {
                "text": "I worry about not knowing what to say in social situations.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "A little bit", "score": 1},
                    {"text": "Somewhat", "score": 2},
                    {"text": "Very much", "score": 3},
                    {"text": "Extremely", "score": 4}
                ]
            },
            {
                "text": "I feel tense when I'm around people I don't know well.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "A little bit", "score": 1},
                    {"text": "Somewhat", "score": 2},
                    {"text": "Very much", "score": 3},
                    {"text": "Extremely", "score": 4}
                ]
            },
            {
                "text": "I have difficulty making eye contact with others.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Not at all", "score": 0},
                    {"text": "A little bit", "score": 1},
                    {"text": "Somewhat", "score": 2},
                    {"text": "Very much", "score": 3},
                    {"text": "Extremely", "score": 4}
                ]
            }
        ],
        "scoring": {
            "name": "Social Anxiety Scale",
            "description": "Assessment of social anxiety symptoms",
            "scoring_method": "sum",
            "max_score": 40,
            "passing_score": 20,
            "rules": [
                {"min": 0, "max": 10, "label": "Minimal", "color": "#00FF00", "description": "Minimal social anxiety"},
                {"min": 11, "max": 20, "label": "Mild", "color": "#FFFF00", "description": "Mild social anxiety"},
                {"min": 21, "max": 30, "label": "Moderate", "color": "#FFA500", "description": "Moderate social anxiety"},
                {"min": 31, "max": 40, "label": "Severe", "color": "#FF0000", "description": "Severe social anxiety"}
            ]
        }
    },
    {
        "title": "Burnout Assessment",
        "description": "A tool for evaluating professional burnout symptoms.",
        "category": "burnout",
        "estimated_time": 10,
        "questions": [
            {
                "text": "I feel emotionally drained from my work.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 0},
                    {"text": "A few times a year", "score": 1},
                    {"text": "Once a month", "score": 2},
                    {"text": "A few times a month", "score": 3},
                    {"text": "Once a week", "score": 4},
                    {"text": "A few times a week", "score": 5},
                    {"text": "Every day", "score": 6}
                ]
            },
            {
                "text": "I feel used up at the end of the workday.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 0},
                    {"text": "A few times a year", "score": 1},
                    {"text": "Once a month", "score": 2},
                    {"text": "A few times a month", "score": 3},
                    {"text": "Once a week", "score": 4},
                    {"text": "A few times a week", "score": 5},
                    {"text": "Every day", "score": 6}
                ]
            },
            {
                "text": "I feel fatigued when I get up in the morning and have to face another day on the job.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 0},
                    {"text": "A few times a year", "score": 1},
                    {"text": "Once a month", "score": 2},
                    {"text": "A few times a month", "score": 3},
                    {"text": "Once a week", "score": 4},
                    {"text": "A few times a week", "score": 5},
                    {"text": "Every day", "score": 6}
                ]
            },
            {
                "text": "Working with people all day is really a strain for me.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 0},
                    {"text": "A few times a year", "score": 1},
                    {"text": "Once a month", "score": 2},
                    {"text": "A few times a month", "score": 3},
                    {"text": "Once a week", "score": 4},
                    {"text": "A few times a week", "score": 5},
                    {"text": "Every day", "score": 6}
                ]
            },
            {
                "text": "I feel burned out from my work.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 0},
                    {"text": "A few times a year", "score": 1},
                    {"text": "Once a month", "score": 2},
                    {"text": "A few times a month", "score": 3},
                    {"text": "Once a week", "score": 4},
                    {"text": "A few times a week", "score": 5},
                    {"text": "Every day", "score": 6}
                ]
            },
            {
                "text": "I feel frustrated by my job.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 0},
                    {"text": "A few times a year", "score": 1},
                    {"text": "Once a month", "score": 2},
                    {"text": "A few times a month", "score": 3},
                    {"text": "Once a week", "score": 4},
                    {"text": "A few times a week", "score": 5},
                    {"text": "Every day", "score": 6}
                ]
            },
            {
                "text": "I feel I'm working too hard on my job.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 0},
                    {"text": "A few times a year", "score": 1},
                    {"text": "Once a month", "score": 2},
                    {"text": "A few times a month", "score": 3},
                    {"text": "Once a week", "score": 4},
                    {"text": "A few times a week", "score": 5},
                    {"text": "Every day", "score": 6}
                ]
            },
            {
                "text": "I feel like I'm at the end of my rope.",
                "question_type": "single_choice",
                "choices": [
                    {"text": "Never", "score": 0},
                    {"text": "A few times a year", "score": 1},
                    {"text": "Once a month", "score": 2},
                    {"text": "A few times a month", "score": 3},
                    {"text": "Once a week", "score": 4},
                    {"text": "A few times a week", "score": 5},
                    {"text": "Every day", "score": 6}
                ]
            }
        ],
        "scoring": {
            "name": "Burnout Inventory",
            "description": "Assessment of professional burnout",
            "scoring_method": "sum",
            "max_score": 48,
            "passing_score": 17,
            "rules": [
                {"min": 0, "max": 16, "label": "Low", "color": "#00FF00", "description": "Low level of burnout"},
                {"min": 17, "max": 26, "label": "Moderate", "color": "#FFFF00", "description": "Moderate burnout"},
                {"min": 27, "max": 48, "label": "High", "color": "#FF0000", "description": "High level of burnout"}
            ]
        }
    }
]

def create_questionnaires_and_questions():
    """Create questionnaires and questions from the sample data"""
    print("Creating questionnaires and questions...")

    # Get a user to be the creator
    try:
        user = User.objects.get(email="admin@example.com")
    except User.DoesNotExist:
        user = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="admin123",
            first_name="Admin",
            last_name="User"
        )

    # Get or create an organization
    organization, created = Organization.objects.get_or_create(
        name="MindTrack Organization",
        defaults={
            "description": "Main organization for MindTrack",
            "created_by": user
        }
    )

    # Make sure the user is a member of the organization
    OrganizationMember.objects.get_or_create(
        organization=organization,
        user=user,
        defaults={
            "role": "admin",
            "is_active": True
        }
    )

    created_questionnaires = []

    for questionnaire_data in QUESTIONNAIRE_DATA:
        # Create the questionnaire
        questionnaire = Questionnaire.objects.create(
            title=questionnaire_data["title"],
            description=questionnaire_data["description"],
            category=questionnaire_data["category"],
            estimated_time=questionnaire_data["estimated_time"],
            is_active=True,
            is_adaptive=False,
            is_qr_enabled=True,
            is_template=False,
            is_public=True,
            allow_anonymous=True,
            requires_auth=False,
            version=1,
            tags=["sample", questionnaire_data["category"]],
            language="en",
            created_by=user,
            organization=organization
        )

        # Create questions and choices
        for i, question_data in enumerate(questionnaire_data["questions"]):
            question = Question.objects.create(
                survey=questionnaire,
                text=question_data["text"],
                question_type=question_data["question_type"],
                required=True,
                order=i,
                is_scored=True,
                is_visible=True
            )

            # Create choices for the question
            for j, choice_data in enumerate(question_data["choices"]):
                QuestionChoice.objects.create(
                    question=question,
                    text=choice_data["text"],
                    order=j,
                    score=choice_data["score"]
                )

        # Create scoring config
        scoring_data = questionnaire_data["scoring"]
        ScoringConfig.objects.create(
            survey=questionnaire,
            name=scoring_data["name"],
            description=scoring_data["description"],
            scoring_method=scoring_data["scoring_method"],
            max_score=scoring_data["max_score"],
            passing_score=scoring_data["passing_score"],
            rules=scoring_data["rules"],
            is_active=True,
            is_default=True,
            created_by=user
        )

        # Create QR code
        QRCode.objects.create(
            survey=questionnaire,
            name=f"QR Code for {questionnaire.title}",
            description=f"QR Code for accessing {questionnaire.title}",
            url=f"https://mindtrack.com/q/{questionnaire.slug}",
            is_active=True,
            created_by=user
        )

        created_questionnaires.append(questionnaire)
        print(f"Created questionnaire: {questionnaire.title} with {len(questionnaire_data['questions'])} questions")

    return created_questionnaires

# Sample patient data for generating responses
PATIENT_DATA = [
    {"name": "John Smith", "email": "john.smith@example.com", "age": 35, "gender": "male"},
    {"name": "Sarah Johnson", "email": "sarah.j@example.com", "age": 42, "gender": "female"},
    {"name": "Michael Brown", "email": "mbrown@example.com", "age": 28, "gender": "male"},
    {"name": "Emily Davis", "email": "emily.davis@example.com", "age": 31, "gender": "female"},
    {"name": "Robert Wilson", "email": "rwilson@example.com", "age": 45, "gender": "male"},
    {"name": "Jennifer Lee", "email": "jlee@example.com", "age": 39, "gender": "female"},
    {"name": "David Martinez", "email": "dmartinez@example.com", "age": 52, "gender": "male"},
    {"name": "Lisa Anderson", "email": "lisa.a@example.com", "age": 29, "gender": "female"},
    {"name": "James Taylor", "email": "jtaylor@example.com", "age": 33, "gender": "male"},
    {"name": "Patricia Garcia", "email": "pgarcia@example.com", "age": 47, "gender": "female"}
]

def create_responses_and_answers(questionnaires):
    """Create responses and answers for the questionnaires"""
    print("Creating responses and answers...")

    responses_created = []

    for questionnaire in questionnaires:
        # Get all questions for this questionnaire
        questions = Question.objects.filter(survey=questionnaire).order_by('order')

        # Get the scoring config
        scoring_config = ScoringConfig.objects.filter(survey=questionnaire, is_active=True).first()

        # Create 5-10 responses for each questionnaire
        num_responses = random.randint(5, 10)

        for i in range(num_responses):
            # Select a random patient
            patient = random.choice(PATIENT_DATA)

            # Create a response
            response = Response.objects.create(
                survey=questionnaire,
                patient_name=patient["name"],
                patient_email=patient["email"],
                patient_age=patient["age"],
                patient_gender=patient["gender"],
                status="completed",
                completion_time=random.randint(300, 900),  # 5-15 minutes
                ip_address="127.0.0.1",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                completed_at=timezone.now() - timedelta(days=random.randint(1, 30))
            )

            # Create answers for each question
            total_score = 0

            for question in questions:
                # Get choices for this question
                choices = QuestionChoice.objects.filter(question=question).order_by('order')

                if question.question_type == 'single_choice' and choices.exists():
                    # Select a random choice
                    selected_choice = random.choice(choices)

                    # Create the answer
                    answer = Answer.objects.create(
                        response=response,
                        question=question,
                        selected_choice=selected_choice,
                        value={"choice_id": selected_choice.id, "choice_text": selected_choice.text}
                    )

                    # Add to total score
                    total_score += selected_choice.score

                elif question.question_type == 'text':
                    # Create a text answer
                    text_responses = [
                        "I've been feeling okay lately.",
                        "It's been difficult to manage my symptoms.",
                        "I'm doing better than last month.",
                        "I've been struggling with this for a while.",
                        "Some days are better than others."
                    ]

                    answer = Answer.objects.create(
                        response=response,
                        question=question,
                        text_answer=random.choice(text_responses),
                        value={"text": random.choice(text_responses)}
                    )

            # Update the response with the score
            response.score = total_score

            # Determine risk level based on scoring config
            if scoring_config:
                for rule in scoring_config.rules:
                    if rule["min"] <= total_score <= rule["max"]:
                        if rule["label"] == "Minimal" or rule["label"] == "Low":
                            response.risk_level = "low"
                        elif rule["label"] == "Mild" or rule["label"] == "Moderate":
                            response.risk_level = "medium"
                        else:
                            response.risk_level = "high"
                        break

            response.save()
            responses_created.append(response)

            print(f"Created response for {questionnaire.title} by {patient['name']} with score {total_score}")

    return responses_created

def create_ai_analysis(responses):
    """Create AI analysis for responses"""
    print("Creating AI analysis results...")

    # Create or get the AI model
    ai_model, created = AIModel.objects.get_or_create(
        name="Gemini Pro",
        defaults={
            "description": "Google Gemini Pro AI model for text analysis",
            "model_type": "nlp",
            "version": "1.0",
            "is_active": True
        }
    )

    for response in responses:
        # Get the questionnaire and its category
        questionnaire = response.survey
        category = questionnaire.category

        # Generate analysis based on category and score
        if category == "depression":
            if response.risk_level == "low":
                summary = "The patient shows minimal signs of depression."
                detailed_analysis = "Based on the responses, the patient is experiencing minimal symptoms of depression. They report occasional feelings of sadness or low energy, but these do not significantly impact their daily functioning. The patient maintains interest in activities and has adequate sleep patterns."
                recommendations = "Continue monitoring mood. Practice self-care and maintain social connections. No clinical intervention appears necessary at this time."
            elif response.risk_level == "medium":
                summary = "The patient shows moderate symptoms of depression."
                detailed_analysis = "The assessment indicates moderate depression symptoms. The patient reports persistent feelings of sadness, decreased interest in activities, and some sleep disturbances. These symptoms are affecting daily functioning but not severely. The patient does not report suicidal ideation."
                recommendations = "Consider a follow-up clinical assessment. Cognitive Behavioral Therapy (CBT) might be beneficial. Encourage regular physical activity and social engagement. Monitor for worsening symptoms."
            else:
                summary = "The patient shows severe symptoms of depression requiring immediate attention."
                detailed_analysis = "The assessment reveals severe depression symptoms. The patient reports persistent feelings of hopelessness, significant loss of interest in activities, severe sleep disturbances, and low energy levels. Daily functioning is significantly impaired. There are concerning responses regarding thoughts of self-harm."
                recommendations = "Immediate clinical intervention is recommended. Consider referral to a psychiatrist for medication evaluation. Psychotherapy is strongly recommended. Develop a safety plan and provide crisis resources."

        elif category == "anxiety":
            if response.risk_level == "low":
                summary = "The patient shows minimal signs of anxiety."
                detailed_analysis = "Based on the responses, the patient is experiencing minimal symptoms of anxiety. They report occasional worry but can generally control it. Physical symptoms of anxiety are rare or mild."
                recommendations = "Continue monitoring anxiety levels. Practice relaxation techniques as needed. No clinical intervention appears necessary at this time."
            elif response.risk_level == "medium":
                summary = "The patient shows moderate symptoms of anxiety."
                detailed_analysis = "The assessment indicates moderate anxiety symptoms. The patient reports frequent worry that is difficult to control, some restlessness, and occasional irritability. These symptoms are affecting daily functioning but not severely."
                recommendations = "Consider a follow-up clinical assessment. Cognitive Behavioral Therapy (CBT) might be beneficial. Teach relaxation techniques and mindfulness practices. Monitor for worsening symptoms."
            else:
                summary = "The patient shows severe symptoms of anxiety requiring attention."
                detailed_analysis = "The assessment reveals severe anxiety symptoms. The patient reports constant worry that significantly interferes with daily life, frequent physical symptoms of anxiety, and high levels of restlessness and irritability. Daily functioning is significantly impaired."
                recommendations = "Clinical intervention is recommended. Consider referral to a psychiatrist for medication evaluation. Cognitive Behavioral Therapy (CBT) is strongly recommended. Teach stress management and relaxation techniques."

        elif category == "stress":
            if response.risk_level == "low":
                summary = "The patient shows low levels of perceived stress."
                detailed_analysis = "Based on the responses, the patient is experiencing low levels of stress. They generally feel in control of their life situations and are able to cope with challenges effectively."
                recommendations = "Continue using effective coping strategies. Practice regular self-care activities. No clinical intervention appears necessary at this time."
            elif response.risk_level == "medium":
                summary = "The patient shows moderate levels of perceived stress."
                detailed_analysis = "The assessment indicates moderate stress levels. The patient reports feeling somewhat overwhelmed by responsibilities and occasionally unable to control important aspects of their life. These feelings are affecting well-being but not severely."
                recommendations = "Review and enhance stress management strategies. Consider mindfulness practices and regular physical activity. Time management techniques may be helpful. Monitor for worsening symptoms."
            else:
                summary = "The patient shows high levels of perceived stress requiring attention."
                detailed_analysis = "The assessment reveals high stress levels. The patient reports feeling consistently overwhelmed, unable to cope with demands, and frequently feeling that things are out of control. Daily functioning and well-being are significantly affected."
                recommendations = "Intervention is recommended. Stress management training would be beneficial. Consider referral for counseling. Evaluate work-life balance and identify specific stressors that could be modified."

        # Create insights based on the analysis
        insights = {
            "key_points": [
                "Patient scored in the " + response.risk_level + " range",
                "Primary symptoms include mood disturbances and energy levels",
                "Current coping mechanisms appear " + ("adequate" if response.risk_level == "low" else "insufficient")
            ],
            "risk_factors": [
                "Age and gender demographics",
                "Reported symptom duration",
                "Severity of functional impairment"
            ],
            "protective_factors": [
                "Social support system",
                "Previous treatment response",
                "Coping skills"
            ]
        }

        # Create the AI analysis
        analysis = AIAnalysis.objects.create(
            response=response,
            summary=summary,
            detailed_analysis=detailed_analysis,
            recommendations=recommendations,
            insights=insights,
            model_used="Gemini Pro",
            confidence_score=random.uniform(0.7, 0.95)
        )

        # Also create an AIAnalysisResult for the analytics app
        AIAnalysisResult.objects.create(
            response=response,
            ai_model=ai_model,
            result_data={
                "summary": summary,
                "detailed_analysis": detailed_analysis,
                "recommendations": recommendations,
                "insights": insights
            },
            summary=summary,
            confidence_score=random.uniform(0.7, 0.95)
        )

        print(f"Created AI analysis for response {response.id} with risk level {response.risk_level}")

def main():
    """Main function to run all data generation"""
    # Create questionnaires and questions
    questionnaires = create_questionnaires_and_questions()

    # Create responses and answers
    responses = create_responses_and_answers(questionnaires)

    # Create AI analysis
    create_ai_analysis(responses)

    print("Data generation complete!")

if __name__ == "__main__":
    main()
