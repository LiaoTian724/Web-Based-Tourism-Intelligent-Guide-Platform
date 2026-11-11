"""Persistent accounts, attraction catalogue and saved walking itineraries."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Category(models.TextChoices):
    HISTORY = "history", "历史建筑"
    CULTURE = "culture", "文化地标"
    PHOTOGRAPHY = "photography", "摄影打卡"
    FOOD = "food", "美食体验"


class Region(models.TextChoices):
    PENINSULA = "peninsula", "澳门半岛"
    TAIPA = "taipa", "氹仔"
    COLOANE = "coloane", "路环"


class SightType(models.TextChoices):
    MUSEUMS = "museums", "博物馆及展览厅"
    CHURCHES = "churches", "教堂"
    TEMPLES = "temples", "庙宇"
    PARKS = "parks", "公园"
    FORTRESSES = "fortresses", "炮台"
    OTHER = "other", "其他景点"


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    interests = models.JSONField(default=list, blank=True)


class Attraction(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField("景点名称", max_length=120)

    name_en = models.CharField("英文名称", max_length=160, blank=True)

    category = models.CharField("分类", max_length=16, choices=Category)

    sight_type = models.CharField("观光分类", max_length=12, choices=SightType, blank=True, default="")

    world_heritage = models.BooleanField("澳门世界遗产", default=False)

    region = models.CharField("区域", max_length=12, choices=Region, default=Region.PENINSULA)

    less_known = models.BooleanField("小众地点", default=False)

    summary = models.CharField("简介", max_length=240)

    history = models.TextField("历史与文化")

    address = models.CharField("地址", max_length=200)

    hours = models.CharField("开放信息", max_length=200)

    admission = models.CharField("门票", max_length=100)

    visit_minutes = models.PositiveSmallIntegerField("建议停留分钟", default=30)

    latitude = models.DecimalField("纬度", max_digits=8, decimal_places=6)

    longitude = models.DecimalField("经度", max_digits=9, decimal_places=6)

    source_url = models.URLField("资料来源", blank=True)

    artwork = models.CharField("插画样式", max_length=24, blank=True)

    enabled = models.BooleanField("公开显示", default=True)


    def clean(self):
        if self.visit_minutes < 5:
            raise ValidationError({
                "visit_minutes": "建议停留时间不能少于5分钟"
            })

        if self.latitude is not None:
            if self.latitude < -90 or self.latitude > 90:
                raise ValidationError({
                    "latitude": "纬度必须在 -90 到 90 之间"
                })

        if self.longitude is not None:
            if self.longitude < -180 or self.longitude > 180:
                raise ValidationError({
                    "longitude": "经度必须在 -180 到 180 之间"
                })

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Itinerary(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="itineraries")
    budget_minutes = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class ItineraryStop(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name="stops")
    attraction = models.ForeignKey(Attraction, on_delete=models.PROTECT)
    position = models.PositiveSmallIntegerField()
    walk_minutes = models.PositiveSmallIntegerField()
    visit_minutes = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["itinerary", "position"], name="unique_stop_position"),
            models.UniqueConstraint(fields=["itinerary", "attraction"], name="unique_itinerary_attraction"),
        ]


class ListingKind(models.TextChoices):
    FOOD = "food", "美食"
    PRODUCT = "product", "文创"


class FoodGroup(models.TextChoices):
    PORTUGUESE = "portuguese", "土生菜及葡国菜"
    SNACKS = "snacks", "地道小吃"
    CAFES = "cafes", "茶餐厅与粉面"


class LocalListing(models.Model):
    kind = models.CharField("类型", choices=ListingKind, max_length=10)
    slug = models.SlugField(unique=True)
    name = models.CharField("名称", max_length=120)
    summary = models.CharField("简介", max_length=240)
    label = models.CharField("类别或创作者", max_length=100)
    food_group = models.CharField("美食分类", max_length=12, choices=FoodGroup, blank=True, default="")
    address = models.CharField("地址", max_length=200, blank=True)
    price = models.CharField("参考价格", max_length=100, blank=True)
    area = models.CharField("区域", max_length=12, choices=Region, default=Region.PENINSULA)
    source_url = models.URLField("资料来源", blank=True)
    image_key = models.SlugField("本地示意图编号", max_length=32, blank=True)
    latitude = models.FloatField("纬度", null=True, blank=True, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.FloatField("经度", null=True, blank=True, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    enabled = models.BooleanField("公开显示", default=True)

    def __str__(self):
        return self.name


class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listing_bookmarks")
    listing = models.ForeignKey(LocalListing, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "listing"], name="one_listing_bookmark")]


class ReviewStatus(models.TextChoices):
    PENDING = "pending", "待审核"
    APPROVED = "approved", "已通过"
    REJECTED = "rejected", "已拒绝"


class ReviewAdvice(models.TextChoices):
    CLEAR = "clear", "未发现明显问题"
    PROMOTION = "promotion", "疑似广告或引流"
    PRIVACY = "privacy", "疑似涉及个人隐私"
    HARASSMENT = "harassment", "疑似骚扰、攻击或仇恨言论"
    OFF_TOPIC = "off_topic", "疑似与游览或消费体验无关"
    UNCERTAIN = "uncertain", "信息不足，无法判断"


class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    attraction = models.ForeignKey(Attraction, null=True, blank=True, on_delete=models.CASCADE, related_name="reviews")
    listing = models.ForeignKey(LocalListing, null=True, blank=True, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    body = models.CharField("评价", max_length=500)
    status = models.CharField("审核状态", max_length=10, choices=ReviewStatus, default=ReviewStatus.PENDING)
    ai_advice = models.CharField("AI 建议原因", max_length=16, choices=ReviewAdvice, blank=True, default="", editable=False)
    ai_advised_at = models.DateTimeField("AI 建议时间", null=True, blank=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]
        constraints = [
            models.CheckConstraint(condition=(
                models.Q(attraction__isnull=False, listing__isnull=True)
                | models.Q(attraction__isnull=True, listing__isnull=False)
            ), name="one_review_target"),
            models.CheckConstraint(condition=models.Q(rating__gte=1, rating__lte=5), name="rating_between_one_and_five"),
            models.UniqueConstraint(fields=["user", "attraction"], condition=models.Q(attraction__isnull=False), name="one_review_per_attraction"),
            models.UniqueConstraint(fields=["user", "listing"], condition=models.Q(listing__isnull=False), name="one_review_per_listing"),
        ]


class ReviewNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_notifications")
    target_name = models.CharField(max_length=120)
    status = models.CharField(max_length=10, choices=[
        (ReviewStatus.APPROVED, ReviewStatus.APPROVED.label),
        (ReviewStatus.REJECTED, ReviewStatus.REJECTED.label),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [models.Index(fields=["user", "read_at"])]
        constraints = [models.CheckConstraint(
            condition=models.Q(status__in=[ReviewStatus.APPROVED, ReviewStatus.REJECTED]),
            name="review_notification_requires_decision",
        )]


class GuideSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guide_sessions")
    title = models.CharField(max_length=90)
    updated_at = models.DateTimeField(auto_now=True)


class GuideExchange(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guide_exchanges")
    session = models.ForeignKey(GuideSession, null=True, blank=True, on_delete=models.CASCADE, related_name="exchanges")
    question = models.CharField(max_length=400)
    answer = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        indexes = [models.Index(fields=["user", "created_at"])]


class AIItineraryDraft(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_itinerary_drafts")
    request_text = models.CharField(max_length=300)
    budget_minutes = models.PositiveSmallIntegerField()
    result = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-id"]
        indexes = [models.Index(fields=["user", "created_at"])]
