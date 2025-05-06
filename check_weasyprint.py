import sys

try:
    import weasyprint
    print(f"WeasyPrint is installed. Version: {weasyprint.__version__}")
    print(f"Path: {weasyprint.__file__}")
    sys.exit(0)
except ImportError as e:
    print(f"WeasyPrint is not installed or not properly detected: {e}")
    sys.exit(1)
