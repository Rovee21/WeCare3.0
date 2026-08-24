import logging

import requests
from django.utils import timezone

logger = logging.getLogger(__name__)

EXPO_PUSH_SEND_URL = "https://exp.host/--/api/v2/push/send"
EXPO_PUSH_TIMEOUT_SECONDS = 10


def send_push_notification(participant, title, body, data=None):
    """
    Sends a push notification to a single participant via Expo's push API.

    Returns a result dict:
      - {"success": False, "reason": "no_token"} if the participant has no push_token
      - {"success": False, "reason": "http_error"/"network_error", "detail": ...} on failure
      - {"success": True, "ticket_id": ..., "ticket_status": "ok"} on a successful send

    Note: a successful response here only means Expo *accepted* the notification for
    delivery (a "ticket"), not that it was actually delivered to the device. Confirming
    delivery requires a follow-up call to Expo's getReceipts endpoint with the ticket id —
    intentionally not done here (would add several seconds of latency per call); could be
    added later as a separate periodic task if delivery-failure tracking becomes important.
    """
    if not participant.push_token:
        logger.warning("send_push_notification: participant %s has no push_token", participant.pk)
        return {"success": False, "reason": "no_token"}

    payload = {
        "to": participant.push_token,
        "title": title,
        "body": body,
        "sound": "default",
    }
    if data:
        payload["data"] = data

    try:
        response = requests.post(EXPO_PUSH_SEND_URL, json=payload, timeout=EXPO_PUSH_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        logger.error("send_push_notification: network error sending to participant %s: %s", participant.pk, exc)
        return {"success": False, "reason": "network_error", "detail": str(exc)}

    if response.status_code != 200:
        logger.error(
            "send_push_notification: Expo returned HTTP %s for participant %s: %s",
            response.status_code, participant.pk, response.text,
        )
        return {"success": False, "reason": "http_error", "detail": response.text}

    body_json = response.json()
    ticket = body_json.get("data")

    if not ticket or ticket.get("status") != "ok":
        error_message = ticket.get("message") if ticket else "no ticket returned"
        logger.error(
            "send_push_notification: Expo rejected notification for participant %s: %s",
            participant.pk, error_message,
        )
        return {"success": False, "reason": "expo_error", "detail": error_message}

    return {"success": True, "ticket_id": ticket.get("id"), "ticket_status": ticket.get("status")}


def send_push_notification_bulk(participants, title, body, data=None):
    """
    Sends the same notification to multiple participants.

    Skips participants with no push_token rather than failing the whole batch.
    Returns a summary dict: {"sent": int, "skipped_no_token": int, "failed": int}.

    Loops and calls send_push_notification per participant. Expo does support batching
    multiple recipients into a single API request — worth doing later if send volume grows,
    but kept simple (one request per participant) for now.
    """
    summary = {"sent": 0, "skipped_no_token": 0, "failed": 0}

    for participant in participants:
        result = send_push_notification(participant, title, body, data=data)
        if result["success"]:
            summary["sent"] += 1
        elif result["reason"] == "no_token":
            summary["skipped_no_token"] += 1
        else:
            summary["failed"] += 1

    return summary


def status_for_send_result(result):
    from content.models import NotificationLog

    if result["success"]:
        return NotificationLog.STATUS_SENT
    if result["reason"] == "no_token":
        return NotificationLog.STATUS_NO_TOKEN
    return NotificationLog.STATUS_FAILED


def send_and_log_notification(participant, title, body, notification_type=None):
    """
    Sends a push notification via send_push_notification() and creates a NotificationLog
    record reflecting the outcome (sent / failed / skipped_no_token) — win or lose, the
    attempt is always logged so the audit trail never silently loses a send attempt.
    Returns the created NotificationLog instance.
    """
    from content.models import NotificationLog

    if notification_type is None:
        notification_type = NotificationLog.TYPE_MANUAL

    result = send_push_notification(participant, title, body)

    return NotificationLog.objects.create(
        participant=participant,
        notification_type=notification_type,
        title=title,
        push_up=body,
        status=status_for_send_result(result),
        actually_sent_at=timezone.now(),
    )


def send_and_log_notification_bulk(participants, title, body, notification_type=None):
    """
    Sends to multiple participants, creating one NotificationLog row per participant
    reflecting that participant's individual outcome. Returns a dict with the same
    summary shape as send_push_notification_bulk plus the list of NotificationLog
    instances created (one per participant, in order).
    """
    from content.models import NotificationLog

    if notification_type is None:
        notification_type = NotificationLog.TYPE_MANUAL

    summary = {"sent": 0, "skipped_no_token": 0, "failed": 0, "logs": []}

    for participant in participants:
        log = send_and_log_notification(participant, title, body, notification_type=notification_type)
        if log.status == NotificationLog.STATUS_SENT:
            summary["sent"] += 1
        elif log.status == NotificationLog.STATUS_NO_TOKEN:
            summary["skipped_no_token"] += 1
        else:
            summary["failed"] += 1
        summary["logs"].append(log)

    return summary


def schedule_notification(participant, title, body, scheduled_for, notification_type=None):
    """
    Creates a NotificationLog row with status='pending' and the given scheduled_for
    datetime, WITHOUT sending anything yet — send_scheduled_notifications picks it up
    once scheduled_for has passed.

    If scheduled_for is None or already in the past, there's nothing to gain from
    parking it as pending (the management command would just pick it up on its very
    next run), so this delegates straight to send_and_log_notification and sends now.
    Returns the created NotificationLog instance either way.
    """
    from content.models import NotificationLog

    if notification_type is None:
        notification_type = NotificationLog.TYPE_MANUAL

    if not scheduled_for or scheduled_for <= timezone.now():
        return send_and_log_notification(participant, title, body, notification_type=notification_type)

    return NotificationLog.objects.create(
        participant=participant,
        notification_type=notification_type,
        title=title,
        push_up=body,
        status=NotificationLog.STATUS_PENDING,
        scheduled_for=scheduled_for,
    )


def schedule_notification_bulk(participants, title, body, scheduled_for, notification_type=None):
    """
    Creates one pending NotificationLog row per participant for the same scheduled_for
    time (or sends immediately per-participant if scheduled_for is None/past — same
    now-or-later rule as schedule_notification, applied individually).
    Returns the list of created NotificationLog instances, one per participant.
    """
    return [
        schedule_notification(participant, title, body, scheduled_for, notification_type=notification_type)
        for participant in participants
    ]


def process_due_scheduled_notifications():
    """
    Sends any pending NotificationLog rows whose scheduled_for time has passed, updating
    each row's status in place (never creating a new row). Shared by both
    `send_scheduled_notifications` (the manual management command) and
    `trigger_scheduled_notifications` (the HTTP endpoint EventBridge calls), so both
    surfaces stay in sync.

    Returns a summary dict: {"processed": int, "sent": int, "failed": int, "skipped_no_token": int}.
    """
    from content.models import NotificationLog

    due = NotificationLog.objects.filter(
        status=NotificationLog.STATUS_PENDING,
        scheduled_for__lte=timezone.now(),
    )

    summary = {"processed": 0, "sent": 0, "failed": 0, "skipped_no_token": 0}

    for log in due:
        result = send_push_notification(log.participant, log.title, log.push_up)
        log.status = status_for_send_result(result)
        log.actually_sent_at = timezone.now()
        log.save(update_fields=["status", "actually_sent_at"])
        summary[log.status] += 1
        summary["processed"] += 1

    return summary
