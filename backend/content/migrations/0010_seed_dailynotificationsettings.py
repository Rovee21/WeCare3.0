from django.db import migrations


def seed_singleton_row(apps, schema_editor):
    DailyNotificationSettings = apps.get_model("content", "DailyNotificationSettings")
    if not DailyNotificationSettings.objects.exists():
        DailyNotificationSettings.objects.create()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0009_dailynotificationsettings"),
    ]

    operations = [
        migrations.RunPython(seed_singleton_row, noop_reverse),
    ]
