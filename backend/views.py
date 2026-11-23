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
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Itinerary, ItineraryStop

@require_GET
def healthz(request):
    return JsonResponse({"status": "ok", "service": "macau-tourism"})


# 给地点加属性
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
        places = places.filter(Q(name__icontains=query) | Q(name_en__icontains=query) | Q(address__icontains=query))

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



# 接受一组地点的经纬度，自动生成一个 Google Maps 步行导航链接
def google_directions(places):
    if not places:
        return ""

    points = [f"{place.latitude},{place.longitude}" for place in places]
    params = {"api": "1", "destination": points[-1], "travelmode": "walking",}

    if len(points) > 1:     # 多于两个地点, 就把第一个地点作为起点
        params["origin"] = points[0]

    if len(points) > 2:
        params["waypoints"] = "|".join(points[1:-1])

    return ("https://www.google.com/maps/dir/?" + urlencode(params))



@require_POST
def plan(request):
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeError):
        return JsonResponse({"error": "请求格式无效"}, status=400,)

    if not isinstance(data, dict):
        return JsonResponse({"error": "请求必须是 JSON 对象"}, status=400,)
    if not isinstance(data.get("interests", []), list):
        return JsonResponse({"error": "兴趣参数必须是列表"}, status=400,)

    form = PlanForm(data)
    if not form.is_valid():
        return JsonResponse({"error": "兴趣或时间预算无效"}, status=400,)

    # 是否保存行程
    save = data.get("save") is True
    # 保存必须登录
    if save and not request.user.is_authenticated:
        return JsonResponse({"error": "请登录后保存行程"}, status=401,)

    budget = form.cleaned_data["budget_minutes"]
    with transaction.atomic():
        # 重新生成行程
        stops, total_minutes = build_plan(Attraction.objects.filter(enabled=True), set(form.cleaned_data["interests"]), budget,)
        itinerary_id = None

        # 防止景点数据发生变化
        if save and [stop["attraction"].pk for stop in stops] != data.get("stop_ids"):
            return JsonResponse({"error": "景点数据已更新，请重新生成后再保存"}, status=409,)


        # 创建行程及其景点记录
        if save and stops:
            stop_ids = [stop["attraction"].pk for stop in stops]

            # 查找当前用户是否已经保存相同的行程
            existing_trips = request.user.itineraries.filter(budget_minutes=budget).prefetch_related("stops__attraction")

            for existing in existing_trips:
                existing_ids = [stop.attraction_id for stop in existing.stops.all()]
                if existing_ids == stop_ids:
                    return JsonResponse(saved_plan(existing))

            # 不存在重复行程，才创建新记录
            itinerary = Itinerary.objects.create(user=request.user,  budget_minutes=budget)
            ItineraryStop.objects.bulk_create([
                ItineraryStop(itinerary=itinerary, position=index, **stop)
                for index, stop in enumerate(stops, start=1)
            ])

            itinerary_id = itinerary.pk

    return JsonResponse(serialize_plan(stops, total_minutes, itinerary_id))



def saved_plan(itinerary):
    stops = [
        {"attraction": stop.attraction,  "walk_minutes": stop.walk_minutes,  "visit_minutes": stop.visit_minutes,}
        for stop in itinerary.stops.all()
    ]

    total_minutes = sum(stop["walk_minutes"] + stop["visit_minutes"] for stop in stops)
    return serialize_plan(stops, total_minutes, itinerary.pk,)  # 数据库中的景点对象转换成前端能够使用的 JSON 数据



@require_GET
def itineraries(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "请登录后查看行程"}, status=401,)

    trips = request.user.itineraries.prefetch_related("stops__attraction")[:20]
    return JsonResponse({"items": [saved_plan(trip) for trip in trips] })



# 数据库中的景点对象转换成前端能够使用的 JSON 数据
def serialize_plan(stops, total_minutes, itinerary_id=None):
    places = [stop["attraction"] for stop in stops]

# [{'id': 1, 'slug': 'ruins-of-st-pauls', 'name': '大三巴牌坊', 'name_en': 'Ruins of St. Paul’s', 'category': 'history', 'sight_type': 'churches', 'world_heritage': True, 'region': 'peninsula', 'less_known': False, 'summary': '沿石阶走近澳门最具辨识度的教堂立面，读一段澳门的中西交流史。', 'history': '这里原是圣保禄学院相邻的天主之母教堂。教堂毁于 1835 年大火，留存的正面石墙如今是澳门历史城区的一部分。', 'address': '澳门耶稣会纪念广场', 'hours': '09:00–18:00，17:30 停止入场。请以官方公告为准。', 'admission': '牌坊外观免费参观', 'visit_minutes': 35, 'latitude': Decimal('22.197500'), 'longitude': Decimal('113.540830'), 'source_url': 'https://www.macaotourism.gov.mo/en/sightseeing/macao-world-heritage/ruins-of-st-pauls', 'artwork': 'ruins', 'enabled': True}, 
#  {'id': 2, 'slug': 'senado-square', 'name': '议事亭前地', 'name_en': 'Senado Square', 'category': 'photography', 'sight_type': '', 'world_heritage': True, 'region': 'peninsula', 'less_known': False, 'summary': '波浪石砖、浅色建筑和街巷在这里交汇，从广场出发漫步旧城。', 'history': '议事亭前地长期是澳门市中心的重要公共空间。广场连接市政署大楼、仁慈堂及周边传统街区，是认识历史城区城市生活的一站。', 'address': '澳门议事亭前地', 'hours': '室外广场，周边场馆开放时间各异。', 'admission': '免费', 'visit_minutes': 25, 'latitude': Decimal('22.193670'), 'longitude': Decimal('113.539700'), 'source_url': 'https://www.macaotourism.gov.mo/en/step-out-macao/central/senado-square', 'artwork': 'senado', 'enabled': True}, 
#  {'id': 3, 'slug': 'a-ma-temple', 'name': '妈阁庙', 'name_en': 'A-Ma Temple', 'category': 'culture', 'sight_type': 'temples', 'world_heritage': True, 'region': 'peninsula', 'less_known': False, 'summary': '从妈阁前地走进依山而建的庙宇，认识澳门的海洋信仰。', 'history': '妈阁庙由依山分布的殿阁组成，供奉妈祖及其他神祇，展现澳门沿岸居民的多元传统信仰。', 'address': '澳门妈阁前地', 'hours': '请查看官方开放信息及现场公告。', 'admission': '免费', 'visit_minutes': 30, 'latitude': Decimal('22.186110'), 'longitude': Decimal('113.531510'), 'source_url': 'https://www.macaotourism.gov.mo/en/sightseeing/macao-world-heritage/a-ma-temple', 'artwork': 'ama', 'enabled': True}]
    return {
        "id": itinerary_id,  "total_minutes": total_minutes,
        "navigation_url": (
            google_directions(places)
            if all(place.enabled for place in places)
            else ""
        ),
        "stops": [
            {
              "id": stop["attraction"].pk,  "name": stop["attraction"].name, "enabled": stop["attraction"].enabled,
              "walk_minutes": stop["walk_minutes"], "visit_minutes": stop["visit_minutes"],
            }
            for stop in stops
        ],
    }




# Markdown 下载
def markdown_download(lines, filename):
    return HttpResponse("\n".join(lines) + "\n",  content_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"',},
    )



# 导出行程计划
@require_GET
def export_itinerary(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "请登录后下载行程"}, status=401,)

    trip = get_object_or_404(request.user.itineraries, pk=pk,)
    data = saved_plan(trip)
    lines = ["# 澳门步行行程", "", f"预计总时长：{data['total_minutes']} 分钟（交通为估算）", "",]

    for index, stop in enumerate(data["stops"], start=1):
        unavailable = ("（景点已下架）" if not stop["enabled"] else "")

        lines.append(
            f"{index}. {stop['name']}{unavailable}"
            f" · 步行约 {stop['walk_minutes']} 分钟"
            f" · 停留 {stop['visit_minutes']} 分钟"
        )

    return markdown_download(lines, f"macau-itinerary-{pk}.md",)