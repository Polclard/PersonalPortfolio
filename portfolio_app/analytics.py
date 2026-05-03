import hashlib
import hmac
import json
from datetime import timedelta

from django.conf import settings
from django.db.models import F
from django.utils import timezone

from .models import ClickEvent, DailyClickAggregate, DailyPageVisit, PageVisit


USER_AGENT_MAX_LENGTH = 255
REFERRER_MAX_LENGTH = 255
TARGET_URL_MAX_LENGTH = 500


def get_raw_retention_days():
    try:
        configured_days = int(getattr(settings, "ANALYTICS_RAW_RETENTION_DAYS", 30))
    except (TypeError, ValueError):
        configured_days = 30
    return max(7, min(configured_days, 30))


def truncate_value(value, max_length):
    return (value or "")[:max_length]


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def hash_ip(ip_address):
    if not ip_address:
        return ""
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        ip_address.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def parse_click_payload(request):
    if request.POST:
        return request.POST
    if not request.body:
        return {}
    return json.loads(request.body)


def _increment_counter(model_class, lookup, count_field):
    obj, created = model_class.objects.get_or_create(
        **lookup,
        defaults={count_field: 1},
    )
    if not created:
        model_class.objects.filter(pk=obj.pk).update(**{count_field: F(count_field) + 1})


def record_page_visit(request):
    if not request.session.session_key:
        request.session.save()

    path = truncate_value(request.path, 255)
    ip_hash = hash_ip(get_client_ip(request))
    session_key = truncate_value(request.session.session_key or "", 100)
    user_agent = truncate_value(request.META.get("HTTP_USER_AGENT", ""), USER_AGENT_MAX_LENGTH)
    referrer = truncate_value(request.META.get("HTTP_REFERER", ""), REFERRER_MAX_LENGTH)

    PageVisit.objects.create(
        path=path,
        method=truncate_value(request.method, 10),
        ip_hash=ip_hash,
        user_agent=user_agent,
        referrer=referrer,
        session_key=session_key,
    )

    _increment_counter(
        DailyPageVisit,
        {
            "date": timezone.localdate(),
            "path": path,
        },
        "visit_count",
    )


def record_click_event(request, payload):
    if not request.session.session_key:
        request.session.save()

    element = truncate_value(payload.get("element", ""), 255)
    element_id = truncate_value(payload.get("element_id", ""), 255)
    element_class = truncate_value(payload.get("element_class", ""), 255)
    text = truncate_value(payload.get("text", ""), 255)
    page = truncate_value(payload.get("page", ""), 255)
    target_url = truncate_value(payload.get("target_url", ""), TARGET_URL_MAX_LENGTH)
    ip_hash = hash_ip(get_client_ip(request))
    session_key = truncate_value(request.session.session_key or "", 100)
    user_agent = truncate_value(request.META.get("HTTP_USER_AGENT", ""), USER_AGENT_MAX_LENGTH)
    referrer = truncate_value(request.META.get("HTTP_REFERER", ""), REFERRER_MAX_LENGTH)

    ClickEvent.objects.create(
        element=element,
        element_id=element_id,
        element_class=element_class,
        text=text,
        page=page,
        target_url=target_url,
        ip_hash=ip_hash,
        user_agent=user_agent,
        referrer=referrer,
        session_key=session_key,
    )

    _increment_counter(
        DailyClickAggregate,
        {
            "date": timezone.localdate(),
            "page": page,
            "element": element,
            "target_url": target_url,
        },
        "click_count",
    )


def cleanup_raw_analytics(now=None):
    now = now or timezone.now()
    cutoff = now - timedelta(days=get_raw_retention_days())
    deleted_page_visits, _ = PageVisit.objects.filter(visited_at__lt=cutoff).delete()
    deleted_click_events, _ = ClickEvent.objects.filter(clicked_at__lt=cutoff).delete()
    return {
        "cutoff": cutoff,
        "deleted_page_visits": deleted_page_visits,
        "deleted_click_events": deleted_click_events,
    }
