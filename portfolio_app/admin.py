from collections import Counter
from django.contrib import admin
from django.db.models import Count, Sum
from django.http import HttpResponseRedirect
from django.urls import path
from types import MethodType

from .analytics import get_raw_retention_days
from .models import (
    ClickEvent,
    DailyClickAggregate,
    DailyPageVisit,
    Education,
    Languages,
    PageVisit,
    Project,
    Skill,
    Technologies,
    TechnologiesForProject,
    WorkExperience,
)

admin.site.register(Skill)
admin.site.register(Technologies)
admin.site.register(WorkExperience)
admin.site.register(TechnologiesForProject)
admin.site.register(Project)
admin.site.register(Education)
admin.site.register(Languages)


@admin.register(DailyPageVisit)
class DailyPageVisitAdmin(admin.ModelAdmin):
    list_display = ("date", "path", "visit_count")
    list_filter = ("date",)
    search_fields = ("path",)
    ordering = ("-date", "-visit_count")
    readonly_fields = ("date", "path", "visit_count")


@admin.register(DailyClickAggregate)
class DailyClickAggregateAdmin(admin.ModelAdmin):
    list_display = ("date", "page", "element", "target_url", "click_count")
    list_filter = ("date", "page", "element")
    search_fields = ("page", "element", "target_url")
    ordering = ("-date", "-click_count")
    readonly_fields = ("date", "page", "element", "target_url", "click_count")


@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    list_display = ("path", "method", "short_ip_hash", "session_key", "visited_at")
    list_filter = ("method", "visited_at", "path")
    search_fields = ("path", "ip_hash", "user_agent", "referrer", "session_key")
    ordering = ("-visited_at",)

    @admin.display(description="Visitor")
    def short_ip_hash(self, obj):
        return obj.ip_hash[:12] if obj.ip_hash else "-"


@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    list_display = ("element", "text", "page", "short_ip_hash", "session_key", "clicked_at")
    list_filter = ("clicked_at", "page", "element")
    search_fields = (
        "element",
        "element_id",
        "element_class",
        "text",
        "page",
        "ip_hash",
        "user_agent",
        "session_key",
    )
    ordering = ("-clicked_at",)

    @admin.display(description="Visitor")
    def short_ip_hash(self, obj):
        return obj.ip_hash[:12] if obj.ip_hash else "-"


def build_chart_points(series):
    if not series:
        return []

    max_total = max(row["total"] for row in series) or 1
    chart_points = []
    for row in series:
        chart_points.append(
            {
                "label": row["date"].strftime("%b %d"),
                "total": row["total"],
                "height_pct": max(8, round((row["total"] / max_total) * 100)),
            }
        )
    return chart_points


def build_series_dataset(series):
    return {
        "labels": [row["date"].strftime("%b %d") for row in series],
        "values": [row["total"] for row in series],
    }


def build_combined_daily_datasets(visit_series, click_series):
    ordered_days = sorted({row["date"] for row in visit_series} | {row["date"] for row in click_series})
    visit_totals = {row["date"]: row["total"] for row in visit_series}
    click_totals = {row["date"]: row["total"] for row in click_series}
    return {
        "labels": [day.strftime("%b %d") for day in ordered_days],
        "visit_values": [visit_totals.get(day, 0) for day in ordered_days],
        "click_values": [click_totals.get(day, 0) for day in ordered_days],
    }


def build_weekday_dataset(series):
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    counts = Counter()
    for row in series:
        counts[row["date"].weekday()] += row["total"]
    return {
        "labels": weekday_names,
        "values": [counts.get(index, 0) for index in range(7)],
    }


def get_analytics_context():
    raw_retention_days = get_raw_retention_days()
    all_time_visit_series = list(
        DailyPageVisit.objects.values("date")
        .annotate(total=Sum("visit_count"))
        .order_by("date")
    )
    all_time_click_series = list(
        DailyClickAggregate.objects.values("date")
        .annotate(total=Sum("click_count"))
        .order_by("date")
    )

    visit_series = list(
        DailyPageVisit.objects.values("date")
        .annotate(total=Sum("visit_count"))
        .order_by("-date")[:14]
    )
    click_series = list(
        DailyClickAggregate.objects.values("date")
        .annotate(total=Sum("click_count"))
        .order_by("-date")[:14]
    )

    visit_series.reverse()
    click_series.reverse()

    visitor_rows = list(
        PageVisit.objects.exclude(ip_hash="").values("ip_hash", "session_key")
        .annotate(
            visits=Count("id"),
        )
        .order_by("-visits")[:10]
    )

    click_counts_by_session = {
        row["session_key"]: row["total"]
        for row in ClickEvent.objects.values("session_key")
        .annotate(total=Count("id"))
        .order_by()
        if row["session_key"]
    }
    click_counts_by_ip_hash = {
        row["ip_hash"]: row["total"]
        for row in ClickEvent.objects.values("ip_hash")
        .annotate(total=Count("id"))
        .order_by()
        if row["ip_hash"]
    }

    for row in visitor_rows:
        row["click_count"] = click_counts_by_session.get(row["session_key"], 0)
        if not row["click_count"]:
            row["click_count"] = click_counts_by_ip_hash.get(row["ip_hash"], 0)
        row["visitor_label"] = row["ip_hash"][:12]

    visit_chart_points = build_chart_points(visit_series)
    click_chart_points = build_chart_points(click_series)

    top_pages = list(
        DailyPageVisit.objects.values("path").annotate(total=Sum("visit_count")).order_by("-total")[:10]
    )
    top_click_targets = list(
        DailyClickAggregate.objects.values("element", "page", "target_url")
        .annotate(total=Sum("click_count"))
        .order_by("-total")[:10]
    )

    combined_daily_dataset = build_combined_daily_datasets(visit_series, click_series)
    visit_daily_dataset = build_series_dataset(visit_series)
    click_daily_dataset = build_series_dataset(click_series)
    visit_weekday_dataset = build_weekday_dataset(all_time_visit_series)
    click_weekday_dataset = build_weekday_dataset(all_time_click_series)
    traffic_share_dataset = {
        "labels": [row["path"] or "/" for row in top_pages[:5]],
        "values": [row["total"] for row in top_pages[:5]],
    }

    return {
        "title": "Analytics Dashboard",
        "total_visits": DailyPageVisit.objects.aggregate(total=Sum("visit_count"))["total"] or 0,
        "total_clicks": DailyClickAggregate.objects.aggregate(total=Sum("click_count"))["total"] or 0,
        "unique_sessions": PageVisit.objects.exclude(session_key="").values("session_key").distinct().count(),
        "unique_visitors": PageVisit.objects.exclude(ip_hash="").values("ip_hash").distinct().count(),
        "raw_retention_days": raw_retention_days,
        "top_pages": top_pages,
        "top_click_targets": top_click_targets,
        "recent_clicks": ClickEvent.objects.order_by("-clicked_at")[:20],
        "recent_visits": PageVisit.objects.order_by("-visited_at")[:20],
        "visitor_rows": visitor_rows,
        "visit_series": visit_series,
        "click_series": click_series,
        "visit_chart_points": visit_chart_points,
        "click_chart_points": click_chart_points,
        "combined_daily_dataset": combined_daily_dataset,
        "visit_daily_dataset": visit_daily_dataset,
        "click_daily_dataset": click_daily_dataset,
        "visit_weekday_dataset": visit_weekday_dataset,
        "click_weekday_dataset": click_weekday_dataset,
        "traffic_share_dataset": traffic_share_dataset,
    }


original_admin_index = admin.site.index


def analytics_admin_index(self, request, extra_context=None):
    context = {
        **get_analytics_context(),
        **(extra_context or {}),
    }
    return original_admin_index(request, extra_context=context)


def analytics_dashboard(request):
    return HttpResponseRedirect("/admin/")


def get_admin_urls(original_get_urls):
    def _get_urls():
        custom_urls = [
            path(
                "analytics/",
                admin.site.admin_view(analytics_dashboard),
                name="portfolio-analytics",
            ),
        ]
        return custom_urls + original_get_urls()

    return _get_urls


admin.site.index_template = "admin/analytics_dashboard.html"
admin.site.index = MethodType(analytics_admin_index, admin.site)
admin.site.get_urls = get_admin_urls(admin.site.get_urls)
