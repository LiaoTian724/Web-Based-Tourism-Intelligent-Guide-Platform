from django.db import models

# Create your models here.
from django.core.exceptions import ValidationError


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
