"""Fill only empty catalogue tags with conservative, editable suggestions."""

from django.core.management.base import BaseCommand
from django.db import transaction

from backend.models import Attraction, LocalListing
from backend.tagging import suggest_attraction_tags, suggest_listing_tags


class Command(BaseCommand):
    help = "Suggest interest tags for untagged catalogue entries; preserve all existing tags."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Preview suggestions without saving changes.")

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        for model, suggest in ((Attraction, suggest_attraction_tags), (LocalListing, suggest_listing_tags)):
            proposed = applied = remaining = 0
            existing = model.objects.exclude(tags=[]).count()
            for item in model.objects.filter(tags=[]).order_by("pk").iterator():
                tags = suggest(item)
                if not tags:
                    remaining += 1
                    continue
                proposed += 1
                if options["verbosity"] >= 1:
                    self.stdout.write(f"{model.__name__} {item.slug}: {', '.join(tags)}")
                if not dry_run:
                    # Recheck the empty value so concurrent editorial changes win.
                    applied += model.objects.filter(pk=item.pk, tags=[]).update(tags=tags)
            verb = "would update" if dry_run else "updated"
            count = proposed if dry_run else applied
            self.stdout.write(self.style.SUCCESS(
                f"{model.__name__}: {verb} {count}; existing tags preserved {existing}; "
                f"remaining untagged {remaining}."
            ))
        if dry_run:
            self.stdout.write("Dry run: no catalogue or user data was changed.")
