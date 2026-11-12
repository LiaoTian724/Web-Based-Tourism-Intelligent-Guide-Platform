from django.shortcuts import render

# Create your views here.


from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_GET, require_POST

from .models import Attraction, Category, Region

import json
from urllib.parse import urlencode 

from .forms import PlanForm
from .planner import build_plan



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







def google_directions(places):
    if not places:
        return ""

    points = [f"{place.latitude},{place.longitude}" for place in places]
    params = {"api": "1", "destination": points[-1], "travelmode": "walking",}

    if len(points) > 1:
        params["origin"] = points[0]

    if len(points) > 2:
        params["waypoints"] = "|".join(points[1:-1])

    return ("https://www.google.com/maps/dir/?" + urlencode(params))


@require_POST
def plan(request):
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeError):
        return JsonResponse(
            {"error": "请求格式无效"},
            status=400,
        )

    if not isinstance(data, dict):
        return JsonResponse(
            {"error": "请求必须是 JSON 对象"},
            status=400,
        )

    if not isinstance(data.get("interests", []), list):
        return JsonResponse(
            {"error": "兴趣参数必须是列表"},
            status=400,
        )

    form = PlanForm(data)

    if not form.is_valid():
        return JsonResponse(
            {"error": "兴趣或时间预算无效"},
            status=400,
        )

    interests = set(form.cleaned_data["interests"])
    budget = form.cleaned_data["budget_minutes"]

    attractions = Attraction.objects.filter(enabled=True)

    stops, total_minutes = build_plan(
        attractions,
        interests,
        budget,
    )

    places = [stop["attraction"] for stop in stops]

    result = {
        "id": None,
        "total_minutes": total_minutes,
        "navigation_url": google_directions(places),
        "stops": [
            {
                "id": stop["attraction"].pk,
                "name": stop["attraction"].name,
                "enabled": stop["attraction"].enabled,
                "walk_minutes": stop["walk_minutes"],
                "visit_minutes": stop["visit_minutes"],
            }
            for stop in stops
        ],
    }

    return JsonResponse(result)
