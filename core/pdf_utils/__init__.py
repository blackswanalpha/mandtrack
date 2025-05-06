"""
PDF utilities for MindTrack.
"""
import logging
import importlib.util

logger = logging.getLogger(__name__)

# Check if WeasyPrint is available
weasyprint_spec = importlib.util.find_spec("weasyprint")
if weasyprint_spec is not None:
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        WEASYPRINT_AVAILABLE = True
        logger.info("WeasyPrint is installed and available for PDF generation.")
    except ImportError:
        WEASYPRINT_AVAILABLE = False
        logger.warning("WeasyPrint is not installed. PDF generation will not be available.")
else:
    WEASYPRINT_AVAILABLE = False
    logger.warning("WeasyPrint is not installed. PDF generation will not be available.")