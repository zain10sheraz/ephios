"""Seed synthetic test data for the SQE project. Run via scripts/reset_env.ps1.

Accounts (all synthetic, local only):
  admin@localhost        / admin        superuser (from upstream devdata)
  planner@sqe.test       / Planner#2026 Planners group (add_event) - role "Planner"
  volunteer@sqe.test     / Volunteer#2026 Volunteers group - role "Volunteer"
  volunteer2@sqe.test    / Volunteer#2026 Volunteers group - second volunteer
"""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ephios.settings")

import django

django.setup()

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.db import transaction

from ephios.core.management.commands.devdata import create_objects
from ephios.core.models import UserProfile


def make_user(email, name, password, groups):
    user = UserProfile(email=email, display_name=name, date_of_birth=date(1990, 1, 1))
    user.password = make_password(password)
    user.save()
    for g in groups:
        g.user_set.add(user)
    return user


@transaction.atomic
def main():
    if UserProfile.objects.exists():
        sys.exit("Database not empty; run scripts/reset_env.ps1 first.")
    create_objects()  # upstream sample data: admin, groups, event types, 1 event
    planners = Group.objects.get(name="Planners")
    volunteers = Group.objects.get(name="Volunteers")
    make_user("planner@sqe.test", "Paula Planner", "Planner#2026", [planners, volunteers])
    make_user("volunteer@sqe.test", "Victor Volunteer", "Volunteer#2026", [volunteers])
    make_user("volunteer2@sqe.test", "Vera Volunteer", "Volunteer#2026", [volunteers])
    print("Seed complete.")


main()
