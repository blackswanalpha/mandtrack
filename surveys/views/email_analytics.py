from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta, datetime
import json
import logging

from surveys.models.email_schedule import EmailLog, EmailSchedule
from surveys.models import EmailTemplate

logger = logging.getLogger(__name__)

@login_required
def email_analytics_dashboard(request):
    """
    Email analytics dashboard with caching
    """
    # Get date range from request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # Default to last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            logger.warning(f"Invalid date format: {start_date_str} - {end_date_str}")
            pass

    # Format dates for cache key
    start_date_fmt = start_date.strftime('%Y-%m-%d')
    end_date_fmt = end_date.strftime('%Y-%m-%d')

    # Generate cache key
    cache_key = f"email_analytics_dashboard_{start_date_fmt}_{end_date_fmt}"

    # Try to get data from cache
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.debug(f"Using cached data for email analytics dashboard: {cache_key}")
        return render(request, 'surveys/email_analytics_dashboard.html', cached_data)

    # Get email logs for the date range
    email_logs = EmailLog.objects.filter(
        sent_at__gte=start_date,
        sent_at__lte=end_date
    )

    # Calculate statistics
    total_sent = email_logs.count()
    total_opened = email_logs.filter(opened=True).count()
    total_clicked = email_logs.filter(clicked=True).count()

    open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
    click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
    click_to_open_rate = (total_clicked / total_opened * 100) if total_opened > 0 else 0

    # Get email templates
    templates = EmailTemplate.objects.all()

    # Calculate template statistics
    template_stats = []
    for template in templates:
        template_logs = email_logs.filter(template=template)
        template_sent = template_logs.count()
        template_opened = template_logs.filter(opened=True).count()
        template_clicked = template_logs.filter(clicked=True).count()

        template_open_rate = (template_opened / template_sent * 100) if template_sent > 0 else 0
        template_click_rate = (template_clicked / template_sent * 100) if template_sent > 0 else 0

        template_stats.append({
            'template': template,
            'sent': template_sent,
            'opened': template_opened,
            'clicked': template_clicked,
            'open_rate': template_open_rate,
            'click_rate': template_click_rate
        })

    # Get daily statistics for chart
    daily_stats = {}
    current_date = start_date.date()
    end_date_only = end_date.date()

    while current_date <= end_date_only:
        daily_stats[current_date.strftime('%Y-%m-%d')] = {
            'sent': 0,
            'opened': 0,
            'clicked': 0
        }
        current_date += timedelta(days=1)

    # Populate daily statistics
    for log in email_logs:
        date_str = log.sent_at.strftime('%Y-%m-%d')
        if date_str in daily_stats:
            daily_stats[date_str]['sent'] += 1
            if log.opened:
                daily_stats[date_str]['opened'] += 1
            if log.clicked:
                daily_stats[date_str]['clicked'] += 1

    # Prepare chart data
    chart_data = {
        'labels': list(daily_stats.keys()),
        'sent': [daily_stats[date]['sent'] for date in daily_stats],
        'opened': [daily_stats[date]['opened'] for date in daily_stats],
        'clicked': [daily_stats[date]['clicked'] for date in daily_stats]
    }

    # Get scheduled emails
    scheduled_emails = EmailSchedule.objects.filter(
        status__in=['pending', 'sent']
    ).order_by('next_send')

    context = {
        'total_sent': total_sent,
        'total_opened': total_opened,
        'total_clicked': total_clicked,
        'open_rate': round(open_rate, 1),
        'click_rate': round(click_rate, 1),
        'click_to_open_rate': round(click_to_open_rate, 1),
        'template_stats': template_stats,
        'chart_data': json.dumps(chart_data),
        'scheduled_emails': scheduled_emails,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'cache_timestamp': timezone.now().isoformat()
    }

    # Cache the data for 15 minutes (900 seconds)
    cache.set(cache_key, context, 900)
    logger.debug(f"Cached email analytics dashboard data: {cache_key}")

    return render(request, 'surveys/email_analytics_dashboard.html', context)

@login_required
def email_template_analytics(request, template_id):
    """
    Email template analytics with caching
    """
    template = get_object_or_404(EmailTemplate, id=template_id)

    # Get date range from request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # Default to last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            logger.warning(f"Invalid date format: {start_date_str} - {end_date_str}")
            pass

    # Format dates for cache key
    start_date_fmt = start_date.strftime('%Y-%m-%d')
    end_date_fmt = end_date.strftime('%Y-%m-%d')

    # Generate cache key
    cache_key = f"email_template_analytics_{template_id}_{start_date_fmt}_{end_date_fmt}"

    # Try to get data from cache
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.debug(f"Using cached data for email template analytics: {cache_key}")
        return render(request, 'surveys/email_template_analytics.html', cached_data)

    # Get email logs for the template and date range
    email_logs = EmailLog.objects.filter(
        template=template,
        sent_at__gte=start_date,
        sent_at__lte=end_date
    )

    # Calculate statistics
    total_sent = email_logs.count()
    total_opened = email_logs.filter(opened=True).count()
    total_clicked = email_logs.filter(clicked=True).count()

    open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
    click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
    click_to_open_rate = (total_clicked / total_opened * 100) if total_opened > 0 else 0

    # Get daily statistics for chart
    daily_stats = {}
    current_date = start_date.date()
    end_date_only = end_date.date()

    while current_date <= end_date_only:
        daily_stats[current_date.strftime('%Y-%m-%d')] = {
            'sent': 0,
            'opened': 0,
            'clicked': 0
        }
        current_date += timedelta(days=1)

    # Populate daily statistics
    for log in email_logs:
        date_str = log.sent_at.strftime('%Y-%m-%d')
        if date_str in daily_stats:
            daily_stats[date_str]['sent'] += 1
            if log.opened:
                daily_stats[date_str]['opened'] += 1
            if log.clicked:
                daily_stats[date_str]['clicked'] += 1

    # Prepare chart data
    chart_data = {
        'labels': list(daily_stats.keys()),
        'sent': [daily_stats[date]['sent'] for date in daily_stats],
        'opened': [daily_stats[date]['opened'] for date in daily_stats],
        'clicked': [daily_stats[date]['clicked'] for date in daily_stats]
    }

    # Get recent logs
    recent_logs = email_logs.order_by('-sent_at')[:50]

    context = {
        'template': template,
        'total_sent': total_sent,
        'total_opened': total_opened,
        'total_clicked': total_clicked,
        'open_rate': round(open_rate, 1),
        'click_rate': round(click_rate, 1),
        'click_to_open_rate': round(click_to_open_rate, 1),
        'chart_data': json.dumps(chart_data),
        'recent_logs': recent_logs,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'cache_timestamp': timezone.now().isoformat()
    }

    # Cache the data for 15 minutes (900 seconds)
    cache.set(cache_key, context, 900)
    logger.debug(f"Cached email template analytics data: {cache_key}")

    return render(request, 'surveys/email_template_analytics.html', context)
