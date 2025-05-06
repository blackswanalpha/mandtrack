# Cron Jobs for MindTrack

This directory contains cron job configurations for the MindTrack application.

## Installation

To install the cron jobs, follow these steps:

1. Edit the `crontab` file to update the paths to match your installation.
2. Install the crontab using the following command:

```bash
crontab cron/crontab
```

## Available Cron Jobs

### Scheduled Email Processing

Runs every 15 minutes to process and send scheduled emails.

```
*/15 * * * * cd /path/to/mindtrack && /path/to/mindtrack/.venv/bin/python manage.py process_scheduled_emails >> /path/to/mindtrack/logs/cron.log 2>&1
```

### Database Backup

Runs daily at 2 AM to create a backup of the database.

```
0 2 * * * cd /path/to/mindtrack && /path/to/mindtrack/.venv/bin/python manage.py dbbackup >> /path/to/mindtrack/logs/backup.log 2>&1
```

### Cleanup Old Files

Runs weekly at 3 AM on Sundays to clean up old logs and temporary files.

```
0 3 * * 0 cd /path/to/mindtrack && /path/to/mindtrack/.venv/bin/python manage.py cleanup_old_files >> /path/to/mindtrack/logs/cleanup.log 2>&1
```

## Logs

All cron job logs are stored in the `/path/to/mindtrack/logs/` directory. Make sure this directory exists and is writable by the user running the cron jobs.

```bash
mkdir -p /path/to/mindtrack/logs
```

## Monitoring Cron Jobs

You can monitor the output of the cron jobs by checking the log files:

```bash
tail -f /path/to/mindtrack/logs/cron.log
```

## Troubleshooting

If the cron jobs are not running as expected, check the following:

1. Make sure the paths in the crontab file are correct.
2. Check that the log directory exists and is writable.
3. Verify that the Python virtual environment is activated correctly.
4. Check the cron logs for any errors:

```bash
grep CRON /var/log/syslog
```

5. Test the command manually to ensure it works:

```bash
cd /path/to/mindtrack && /path/to/mindtrack/.venv/bin/python manage.py process_scheduled_emails
```
