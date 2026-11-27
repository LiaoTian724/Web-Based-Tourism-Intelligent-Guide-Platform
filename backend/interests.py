"""Shared recommendation vocabulary, independent of itinerary categories."""

from django.core.exceptions import ValidationError
from django.db import models


class InterestTag(models.TextChoices):
    HISTORY = "history", "历史建筑"
    CULTURE = "culture", "文化艺术"
    PHOTOGRAPHY = "photography", "摄影打卡"
    MUSEUM = "museum", "博物馆展览"
    RELIGION = "religion", "宗教文化"
    NATURE = "nature", "自然风光"
    LEISURE = "leisure", "休闲漫步"
    HIDDEN_GEMS = "hidden_gems", "小众探索"
    LOCAL_SNACKS = "local_snacks", "地道小吃"
    PORTUGUESE_FOOD = "portuguese_food", "葡国菜及土生菜"
    CAFE_DESSERT = "cafe_dessert", "咖啡甜品"
    LOCAL_DINING = "local_dining", "茶餐厅及粉面"
    SOUVENIR = "souvenir", "纪念品"
    DESIGN = "design", "艺术设计"
    HANDICRAFT = "handicraft", "传统手工艺"


def validate_interest_tags(value):
    """Reject arbitrary JSON, unknown tags and duplicate feature values."""
    if not isinstance(value, list):
        raise ValidationError("兴趣标签必须是列表。", code="invalid_tags")
    if any(not isinstance(tag, str) or tag not in InterestTag.values for tag in value):
        raise ValidationError("请选择词表中的有效兴趣标签。", code="invalid_tags")
    if len(value) != len(set(value)):
        raise ValidationError("兴趣标签不能重复。", code="duplicate_tags")


def tag_labels(tags):
    return [InterestTag(tag).label for tag in tags if tag in InterestTag.values]
