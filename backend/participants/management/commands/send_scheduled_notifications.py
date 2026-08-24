from django.core.management.base import BaseCommand
from participants.notifications import process_due_scheduled_notifications


class Command(BaseCommand):
    help = "Send any pending NotificationLog rows whose scheduled_for time has passed"

    def handle(self, *args, **kwargs):
        summary = process_due_scheduled_notifications()
        self.stdout.write(self.style.SUCCESS(
            f"Processed {summary['processed']} due notifications: {summary['sent']} sent, "
            f"{summary['failed']} failed, {summary['skipped_no_token']} skipped_no_token"
        ))
