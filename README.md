# MindTrack

MindTrack is a Django-based web application for managing questionnaires, surveys, and feedback.

## Features

- User authentication and management
- Questionnaire creation and management
- QR code generation for questionnaires
- Response collection and analysis
- Organization management
- Dashboard with analytics

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mindtrack.git
   cd mindtrack
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```
   cp .env.example .env
   ```
   Then edit the `.env` file with your settings.

5. Run migrations:
   ```
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

7. Collect static files:
   ```
   python manage.py collectstatic
   ```

## Development

To run the development server:

```
python manage.py runserver
```

## Production Deployment

### Using server.py

The `server.py` script provides a convenient way to run the application in a production environment using Gunicorn.

```
python server.py
```

Options:
- `--host HOST`: Host to bind to (default: 0.0.0.0)
- `--port PORT`: Port to bind to (default: 8000)
- `--workers WORKERS`: Number of worker processes (default: CPU count * 2 + 1)
- `--timeout TIMEOUT`: Worker timeout in seconds (default: 120)
- `--reload`: Enable auto-reload on code changes (development only)
- `--log-level LEVEL`: Log level (default: info)
- `--access-log FILE`: Access log file (default: None)
- `--error-log FILE`: Error log file (default: None)

Example:
```
python server.py --host 127.0.0.1 --port 8000 --workers 4 --log-level debug
```

### Using Gunicorn Directly

```
gunicorn mindtrack.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Using Docker

A Dockerfile is provided for containerized deployment.

```
docker build -t mindtrack .
docker run -p 8000:8000 mindtrack
```

### Heroku Deployment

The application includes a Procfile for Heroku deployment.

```
heroku create
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

## Environment Variables

See `.env.example` for a list of required environment variables.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
