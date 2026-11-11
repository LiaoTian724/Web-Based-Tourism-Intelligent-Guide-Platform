"""Read-only API for Macau food and cultural-product listings."""

from urllib.parse import urlencode

from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import ListingKind, LocalListing, ReviewStatus


def listing_to_dict(item, bookmarked_ids):
    """Convert one LocalListing record into the frontend JSON format."""
    destination = item.address or item.name

    if not item.address and item.latitude is not None and item.longitude is not None:
        destination = f"{item.latitude},{item.longitude}"

    navigation_url = ""
    if item.kind == ListingKind.FOOD:
        navigation_url = "https://www.google.com/maps/dir/?" + urlencode({
            "api": "1",
            "destination": destination,
            "travelmode": "walking",
        })

    return {
        "id": item.pk,
        "name": item.name,
        "kind": item.kind,
        "summary": item.summary,
        "label": item.label,
        "address": item.address,
        "price": item.price,
        "lat": item.latitude,
        "lng": item.longitude,
        "rating": item.rating,
        "review_count": item.review_count,
        "area": item.area,
        "area_label": item.get_area_display(),
        "source_url": item.source_url,
        "food_group": item.food_group,
        "food_group_label": item.get_food_group_display(),
        "image_key": item.image_key,
        "bookmarked": item.pk in bookmarked_ids,
        "navigation_url": navigation_url,
    }


@require_GET
def listings(request):
    """Return all enabled food and cultural-product records."""
    approved_reviews = Q(reviews__status=ReviewStatus.APPROVED)

    items = (
        LocalListing.objects
        .filter(enabled=True)
        .annotate(
            rating=Avg("reviews__rating", filter=approved_reviews),
            review_count=Count("reviews", filter=approved_reviews),
        )
        .order_by("id")
    )

    if request.user.is_authenticated:
        bookmarked_ids = set(
            request.user.listing_bookmarks.values_list("listing_id", flat=True)
        )
    else:
        bookmarked_ids = set()

    data = [listing_to_dict(item, bookmarked_ids) for item in items]

    return JsonResponse({
        "count": len(data),
        "items": data,
    })
