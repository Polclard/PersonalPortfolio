from django.core.management.base import BaseCommand

from portfolio_app.analytics import cleanup_raw_analytics, get_raw_retention_days


class Command(BaseCommand):
    help = "Delete raw analytics rows older than the configured retention window."

    def handle(self, *args, **options):
        result = cleanup_raw_analytics()
        self.stdout.write(
            self.style.SUCCESS(
                "Deleted raw analytics older than "
                f"{get_raw_retention_days()} days: "
                f"{result['deleted_page_visits']} page visits, "
                f"{result['deleted_click_events']} click events."
            )
        )
