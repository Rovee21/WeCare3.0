from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from participants.models import Participant


class Command(BaseCommand):
    help = 'Reset first participant for testing — clears enrollment and generates a fresh code'

    def handle(self, *args, **kwargs):
        p = Participant.objects.first()
        if not p:
            self.stdout.write(self.style.ERROR('No participant found.'))
            return

        # Reset enrollment state
        p.is_enrolled = False
        p.enrolled_at = None
        p.enrollment_code = None
        p.save()

        # Delete existing token so a fresh one is issued on next enroll
        if p.user:
            Token.objects.filter(user=p.user).delete()

        # Generate fresh code
        code = p.generate_enrollment_code()

        self.stdout.write(self.style.SUCCESS(f'Reset {p.participant_id} — new code: {code}'))