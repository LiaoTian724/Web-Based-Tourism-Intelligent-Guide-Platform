from django.shortcuts import render

# Create your views here.


from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_GET

from .models import Attraction, Category, Region


@require_GET
def healthz(request):
    return JsonResponse({"status": "ok", "service": "macau-tourism"})


def attraction_to_dict(place):
    return {
        "id": place.id,
        "slug": place.slug,
        "name": place.name,
        "name_en": place.name_en,
        "category": place.category,
        "category_label": place.get_category_display(),
        "sight_type": place.sight_type,
        "region": place.region,
        "region_label": place.get_region_display(),
        "world_heritage": place.world_heritage,
        "less_known": place.less_known,
        "summary": place.summary,
        "history": place.history,
        "address": place.address,
        "hours": place.hours,
        "admission": place.admission,
        "visit_minutes": place.visit_minutes,
        "lat": float(place.latitude),
        "lng": float(place.longitude),
        "source_url": place.source_url,
        "artwork": place.artwork,
    }


@require_GET
def attractions(request):
    places = Attraction.objects.filter(enabled=True)

    # 搜索
    query = request.GET.get("q", "").strip()[:120]

    if query:
        places = places.filter(
            Q(name__icontains=query)
            | Q(name_en__icontains=query)
            | Q(address__icontains=query)
        )

    # 分类筛选
    category = request.GET.get("category", "")
    if category in Category.values:
        places = places.filter(category=category)

    # 区域筛选
    region = request.GET.get("region", "")
    if region in Region.values:
        places = places.filter(region=region)

    items = [attraction_to_dict(place) for place in places]

    return JsonResponse({"count": len(items), "items": items})
