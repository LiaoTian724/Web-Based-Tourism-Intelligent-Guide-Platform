"""Assign tourism topics to newly created catalogue seed rows."""

from django.core.management.base import BaseCommand
from django.db import transaction

from backend.models import Attraction, FoodGroup, ListingKind, LocalListing, SightType

# Some of the official world heritage listings are also churches, temples,
# forts, or heritage buildings open as exhibitions.
SIGHT_TOPICS = {
    "ruins-of-st-pauls": (SightType.CHURCHES, True),
    "senado-square": ("", True),
    "a-ma-temple": (SightType.TEMPLES, True),
    "mandarins-house": (SightType.MUSEUMS, True),
    "lilau-square": ("", True),
    "lou-kau-mansion": (SightType.MUSEUMS, True),
    "st-dominics-church": (SightType.CHURCHES, True),
    "mount-fortress": (SightType.FORTRESSES, True),
    "guia-fortress": (SightType.FORTRESSES, True),
    "lou-lim-ioc-garden": (SightType.PARKS, False),
    "dom-pedro-v-theatre": ("", True),
    "taipa-houses": (SightType.MUSEUMS, False),
    "iec-long": (SightType.MUSEUMS, False),
    "rua-do-cunha": (SightType.OTHER, False),
    "st-francis-xavier-coloane": (SightType.CHURCHES, False),
}
FOOD_GROUPS = {
    "wong-chi-kei-senado": FoodGroup.CAFES,
    "margarets-cafe-e-nata": FoodGroup.SNACKS,
    "a-lorcha": FoodGroup.PORTUGUESE,
    "ngao-kei": FoodGroup.CAFES,
    "tai-lei-loi-kei": FoodGroup.SNACKS,
    "nam-ping": FoodGroup.CAFES,
}


class Command(BaseCommand):
    help = "Assign known tourism topics to the specified newly seeded slugs."

    def add_arguments(self, parser):
        parser.add_argument("--sight-slugs", nargs="*", default=[], help="Newly created attraction slugs")
        parser.add_argument("--food-slugs", nargs="*", default=[], help="Newly created dining slugs")

    @transaction.atomic
    def handle(self, *args, sight_slugs, food_slugs, **options):
        for slug in set(sight_slugs).intersection(SIGHT_TOPICS):
            sight_type, world_heritage = SIGHT_TOPICS[slug]
            Attraction.objects.filter(slug=slug).update(sight_type=sight_type, world_heritage=world_heritage)
        for slug in set(food_slugs).intersection(FOOD_GROUPS):
            LocalListing.objects.filter(kind=ListingKind.FOOD, slug=slug).update(food_group=FOOD_GROUPS[slug])
