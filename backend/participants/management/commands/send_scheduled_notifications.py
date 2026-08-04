from django.core.management.base import BaseCommand
from django.utils import timezone
from content.models import NotificationLog
from participants.notifications import send_push_notification, status_for_send_result


class Command(BaseCommand):
    help = "Send any pending NotificationLog rows whose scheduled_for time has passed"

    def handle(self, *args, **kwargs):
        due = NotificationLog.objects.filter(
            status=NotificationLog.STATUS_PENDING,
            scheduled_for__lte=timezone.now(),
        )

        counts = {"sent": 0, "failed": 0, "skipped_no_token": 0}

        for log in due:
            result = send_push_notification(log.participant, log.title, log.push_up)
            log.status = status_for_send_result(result)
            log.actually_sent_at = timezone.now()
            log.save(update_fields=["status", "actually_sent_at"])
            counts[log.status] += 1

        total = sum(counts.values())
        self.stdout.write(self.style.SUCCESS(
            f"Processed {total} due notifications: {counts['sent']} sent, "
            f"{counts['failed']} failed, {counts['skipped_no_token']} skipped_no_token"
        ))
