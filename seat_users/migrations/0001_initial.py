# Generated by Django 5.1.6 on 2025-02-18 14:01

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Course",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("course_name", models.CharField(max_length=255)),
                ("branch", models.CharField(max_length=255)),
                ("total_seats", models.IntegerField()),
                ("locked_seats", models.IntegerField(default=0)),
                ("left_seats", models.IntegerField()),
                (
                    "price_per_seat",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "institute_name",
                    models.CharField(default="JEC Jabalpur", max_length=255),
                ),
                ("city", models.CharField(default="Jabalpur", max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("full_name", models.CharField(max_length=255)),
                ("designation", models.CharField(max_length=255)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("phone_number", models.CharField(max_length=20, unique=True)),
                ("company_name", models.CharField(max_length=255)),
                ("password", models.CharField(max_length=255)),
                ("adopted_students", models.IntegerField(default=0)),
                ("role", models.CharField(default="user", max_length=20)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name="Billing",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("selected_courses", models.JSONField()),
                ("total_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("otp", models.CharField(blank=True, max_length=10, null=True)),
                (
                    "payment_status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("completed", "Completed")],
                        default="pending",
                        max_length=10,
                    ),
                ),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="seat_users.user",
                    ),
                ),
            ],
        ),
    ]
