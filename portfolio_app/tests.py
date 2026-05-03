import json
from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .analytics import get_raw_retention_days
from .models import ClickEvent, DailyClickAggregate, DailyPageVisit, PageVisit


class AnalyticsTrackingTests(TestCase):
    def test_portfolio_page_sets_csrf_cookie(self):
        response = self.client.get("/", HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)

    def test_track_click_creates_event_from_form_post(self):
        client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
        page_response = client.get("/")

        response = client.post(
            reverse("track_click"),
            data={
                "element": "A",
                "element_id": "github-link",
                "element_class": "btn primary",
                "text": "GitHub",
                "page": "/",
                "target_url": "https://github.com/example",
                "csrfmiddlewaretoken": page_response.cookies["csrftoken"].value,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ClickEvent.objects.count(), 1)
        self.assertEqual(DailyClickAggregate.objects.count(), 1)
        event = ClickEvent.objects.get()
        self.assertTrue(event.ip_hash)
        self.assertFalse(event.ip_address)

    def test_track_click_requires_csrf(self):
        client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")

        response = client.post(
            reverse("track_click"),
            data={
                "element": "A",
                "text": "Download CV",
                "page": "/",
                "target_url": "/download-cv/",
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_track_click_accepts_json_with_csrf_header(self):
        client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
        page_response = client.get("/")

        response = client.post(
            reverse("track_click"),
            data=json.dumps(
                {
                    "element": "A",
                    "text": "JSON Link",
                    "page": "/",
                    "target_url": "https://example.com",
                }
            ),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=page_response.cookies["csrftoken"].value,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ClickEvent.objects.count(), 1)

    def test_page_visit_creates_raw_and_daily_aggregate(self):
        response = self.client.get("/", HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PageVisit.objects.count(), 1)
        self.assertEqual(DailyPageVisit.objects.count(), 1)
        visit = PageVisit.objects.get()
        self.assertTrue(visit.ip_hash)
        self.assertFalse(visit.ip_address)

    def test_cleanup_command_deletes_old_raw_events_only(self):
        old_timestamp = timezone.now() - timedelta(days=get_raw_retention_days() + 1)
        recent_timestamp = timezone.now()

        old_visit = PageVisit.objects.create(path="/old", method="GET", ip_hash="oldhash")
        old_click = ClickEvent.objects.create(
            element="A",
            page="/old",
            target_url="/download-cv/",
            ip_hash="oldhash",
        )
        recent_visit = PageVisit.objects.create(path="/recent", method="GET", ip_hash="newhash")
        DailyPageVisit.objects.create(date=timezone.localdate(), path="/old", visit_count=3)
        DailyClickAggregate.objects.create(
            date=timezone.localdate(),
            page="/old",
            element="A",
            target_url="/download-cv/",
            click_count=2,
        )

        PageVisit.objects.filter(pk=old_visit.pk).update(visited_at=old_timestamp)
        ClickEvent.objects.filter(pk=old_click.pk).update(clicked_at=old_timestamp)
        PageVisit.objects.filter(pk=recent_visit.pk).update(visited_at=recent_timestamp)

        output = StringIO()
        call_command("cleanup_analytics", stdout=output)

        self.assertFalse(PageVisit.objects.filter(pk=old_visit.pk).exists())
        self.assertFalse(ClickEvent.objects.filter(pk=old_click.pk).exists())
        self.assertTrue(PageVisit.objects.filter(pk=recent_visit.pk).exists())
        self.assertEqual(DailyPageVisit.objects.count(), 1)
        self.assertEqual(DailyClickAggregate.objects.count(), 1)
        self.assertIn("Deleted raw analytics older than", output.getvalue())


class AnalyticsAdminTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password123",
        )

    def test_admin_analytics_dashboard_loads(self):
        self.client.force_login(self.admin_user)

        response = self.client.get("/admin/", HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Analytics Dashboard")
        self.assertContains(response, "All-Time Visits")
        self.assertContains(response, "All-Time Clicks")
        self.assertContains(response, "Raw Retention")
        self.assertContains(response, "Recent Actions")
        self.assertContains(response, "Manage Content")
        self.assertContains(response, "Visits Chart")
        self.assertContains(response, "Clicks Chart")
        self.assertContains(response, "Interactive Trends")
        self.assertContains(response, "Whole Week Activity")
        self.assertContains(response, "Traffic Share")

    def test_admin_analytics_alias_redirects_to_admin_home(self):
        self.client.force_login(self.admin_user)

        response = self.client.get("/admin/analytics/", HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/admin/")
