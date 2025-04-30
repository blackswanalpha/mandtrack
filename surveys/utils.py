import logging
import traceback
import json
from django.forms import model_to_dict

logger = logging.getLogger(__name__)

def log_form_errors(form, prefix="Form errors"):
    """
    Log form errors in a structured way
    """
    errors = {}
    for field, error_list in form.errors.items():
        errors[field] = [str(error) for error in error_list]
    
    logger.error(f"{prefix}: {json.dumps(errors)}")
    return errors

def log_model_creation_attempt(model_instance, form_data=None, prefix="Model creation attempt"):
    """
    Log details about a model instance that's being created
    """
    model_data = model_to_dict(model_instance)
    
    # Remove any sensitive fields if needed
    if 'password' in model_data:
        model_data['password'] = '[REDACTED]'
    
    log_data = {
        'model': model_instance.__class__.__name__,
        'model_data': model_data
    }
    
    if form_data:
        # Clean form data of any sensitive information
        clean_form_data = {k: v for k, v in form_data.items() if k != 'csrfmiddlewaretoken'}
        log_data['form_data'] = clean_form_data
    
    logger.info(f"{prefix}: {json.dumps(log_data)}")
    return log_data

def log_exception(e, prefix="Exception occurred"):
    """
    Log exception details
    """
    logger.error(f"{prefix}: {str(e)}")
    logger.error(traceback.format_exc())
    return str(e)
