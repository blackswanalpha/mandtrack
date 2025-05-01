# HostPinnacle Deployment Guide for MindTrack

This guide provides step-by-step instructions for deploying the MindTrack application on a HostPinnacle server.

## Prerequisites

- A HostPinnacle account with Python hosting
- SSH access to your HostPinnacle server
- Git installed on your local machine
- Basic knowledge of Linux commands

## Deployment Steps

### 1. Set Up Your HostPinnacle Environment

1. Log in to your HostPinnacle control panel
2. Create a new Python application (if not already created)
3. Note your application's domain name and document root path

### 2. Connect to Your Server via SSH

```bash
ssh username@your-hostpinnacle-server.com
```

### 3. Clone the Repository

Navigate to your document root and clone the repository:

```bash
cd /path/to/document/root
git clone https://github.com/blackswanalpha/mandtrack.git .
```

### 4. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Environment Variables

Create a `.env` file in the project root:

```bash
touch .env
nano .env
```

Add the following environment variables:

```
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,mindtrack.barberianspa.com
DATABASE_URL=postgresql://mindtrack_db_owner:npg_AUV4r3qElnDN@ep-steep-base-a2xkorr1-pooler.eu-central-1.aws.neon.tech/mindtrack_db?sslmode=require
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your-smtp-server.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=noreply@mindtrack.com
SITE_URL=https://your-domain.com
```

### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput --settings=mindtrack.hostpinnacle_settings
```

#### Deploying to barberianspa.com

If you're deploying to the barberianspa.com domain, use the barberianspa_settings module instead:

```bash
python manage.py collectstatic --noinput --settings=mindtrack.barberianspa_settings
```

### 8. Run Migrations

```bash
python manage.py migrate --settings=mindtrack.hostpinnacle_settings
```

#### Deploying to barberianspa.com

If you're deploying to the barberianspa.com domain, use the barberianspa_settings module instead:

```bash
python manage.py migrate --settings=mindtrack.barberianspa_settings
```

### 9. Create a Superuser

```bash
python manage.py createsuperuser --settings=mindtrack.hostpinnacle_settings
```

#### Deploying to barberianspa.com

If you're deploying to the barberianspa.com domain, use the barberianspa_settings module instead:

```bash
python manage.py createsuperuser --settings=mindtrack.barberianspa_settings
```

### 10. Configure Passenger

Ensure that the `passenger_wsgi.py` file is in the project root. This file is already included in the repository.

### 11. Set File Permissions

```bash
chmod 755 passenger_wsgi.py
chmod 755 server.py
chmod -R 755 venv
```

### 12. Restart the Application

From your HostPinnacle control panel, restart the Python application.

### 13. Test the Deployment

Visit your domain in a web browser to verify that the application is running correctly.

## Running with Gunicorn (Alternative to Passenger)

If you prefer to use Gunicorn instead of Passenger, you can use the included `server.py` script:

```bash
python server.py --settings=mindtrack.hostpinnacle_settings
```

For production use, you might want to run it with specific parameters:

```bash
python server.py --host=127.0.0.1 --port=8009 --workers=4 --log-level=info --settings=mindtrack.hostpinnacle_settings
```

### Running on barberianspa.com

For the barberianspa.com domain, use the barberianspa_settings module:

```bash
python server.py --host=127.0.0.1 --port=8009 --workers=4 --log-level=info --settings=mindtrack.barberianspa_settings
```

Alternatively, you can use the provided convenience script:

```bash
./run_barberianspa.sh
```

## Troubleshooting

### Application Not Starting

Check the logs in your HostPinnacle control panel or the log files in your application directory:

```bash
cat hostpinnacle.log
cat passenger_wsgi.log
```

### Database Connection Issues

Verify your database connection settings in `mindtrack/hostpinnacle_settings.py` and ensure that your database is accessible from the HostPinnacle server.

### Static Files Not Loading

Make sure you've run the `collectstatic` command and that the `STATIC_ROOT` directory exists and is properly configured in your settings.

### Permission Issues

Ensure that all necessary files and directories have the correct permissions:

```bash
chmod -R 755 .
find . -type f -name "*.py" -exec chmod 755 {} \;
```

## Maintenance

### Updating the Application

To update the application:

```bash
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py collectstatic --noinput --settings=mindtrack.hostpinnacle_settings
python manage.py migrate --settings=mindtrack.hostpinnacle_settings
```

Then restart the application from your HostPinnacle control panel.

### Backing Up the Database

It's recommended to set up regular backups of your database. If you're using Neon PostgreSQL, you can use their built-in backup features.

### Monitoring

Monitor your application's performance and logs regularly to ensure it's running smoothly.

## Security Considerations

- Keep your Django secret key secure and never commit it to version control
- Regularly update your dependencies to patch security vulnerabilities
- Use HTTPS for all traffic
- Implement proper authentication and authorization mechanisms
- Regularly back up your database

## Support

If you encounter any issues with your HostPinnacle deployment, contact HostPinnacle support or refer to their documentation for assistance.
