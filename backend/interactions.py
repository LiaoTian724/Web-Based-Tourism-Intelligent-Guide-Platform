"""Record explicit views by signed-in visitors."""

import json
from uuid import UUID

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Attraction, InteractionAction, LocalListing, UserInteraction


@require_POST
def user_interaction(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "请先登录"}, status=401)

    if request.content_type != "application/json":
        return JsonResponse({"error": "请使用 JSON 提交浏览记录"}, status=400)

    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeError):
        return JsonResponse({"error": "请求格式无效"}, status=400)

    required_fields = {"target_type", "target_id", "action"}
    if (
        not isinstance(data, dict)
        or not required_fields.issubset(data)
        or set(data) - required_fields - {"impression_id"}
    ):
        return JsonResponse({"error": "浏览记录字段无效"}, status=400)

    target_type = data["target_type"]
    target_id = data["target_id"]
    target_models = {"attraction": Attraction, "listing": LocalListing}
    if (
        not isinstance(target_type, str)
        or target_type not in target_models
        or type(target_id) is not int
        or target_id <= 0
        or data["action"] != InteractionAction.VIEW
    ):
        return JsonResponse({"error": "浏览对象或操作无效"}, status=400)

    impression_id = None
    if "impression_id" in data:
        if not isinstance(data["impression_id"], str):
            return JsonResponse({"error": "浏览标识必须是有效 UUID"}, status=400)
        try:
            impression_id = UUID(data["impression_id"])
        except ValueError:
            return JsonResponse({"error": "浏览标识必须是有效 UUID"}, status=400)

    target = target_models[target_type].objects.filter(pk=target_id, enabled=True).first()
    if target is None:
        return JsonResponse({"error": "内容不存在"}, status=404)

    interaction = UserInteraction.objects.create(
        user=request.user,
        action=InteractionAction.VIEW,
        impression_id=impression_id,
        **{target_type: target},
    )
    return JsonResponse({"recorded": True, "id": interaction.pk}, status=201)
