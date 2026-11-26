"""Create editable dining and cultural-product examples."""

from django.core.management.base import BaseCommand
from django.db import transaction

from backend.models import ListingKind, LocalListing


LISTINGS = [
    {
        "slug": "wong-chi-kei-senado", "kind": ListingKind.FOOD,
        "name": "黄枝记 · 议事亭前地", "label": "广式粥面",
        "summary": "在议事亭前地附近找一顿简便的粥面，可从云吞面和粥类入手。",
        "address": "澳门议事亭前地 17 号地下", "latitude": 22.19362, "longitude": 113.53975,
    },
    {
        "slug": "margarets-cafe-e-nata", "kind": ListingKind.FOOD,
        "name": "玛嘉烈蛋挞", "label": "葡挞与烘焙",
        "summary": "澳门半岛的葡挞店，适合安排在新马路一带的步行行程中。",
        "address": "澳门马统领围 66 号，金利来大厦 17B 地铺", "latitude": 22.19324, "longitude": 113.54273,
    },
    {
        "slug": "a-lorcha", "kind": ListingKind.FOOD,
        "name": "船屋葡国餐厅", "label": "葡式料理",
        "summary": "位于妈阁附近的葡式餐厅，可作为参观妈阁庙后的正餐选择。",
        "address": "澳门河边新街 289-AA 号地下", "latitude": 22.18671, "longitude": 113.53092,
    },
    {
        "slug": "azulejo-postcards", "kind": ListingKind.PRODUCT,
        "name": "葡砖纹样明信片", "label": "澳門漫遊课程设计",
        "summary": "以蓝白葡砖与澳门旧城街巷为灵感的一组旅行明信片。",
        "price": "MOP 28 · 模拟售价",
    },
    {
        "slug": "heritage-stamp-book", "kind": ListingKind.PRODUCT,
        "name": "澳门历史城区集章册", "label": "澳門漫遊课程设计",
        "summary": "以牌坊、广场和庙宇为主题的步行记录册，留出手绘、盖章和路线笔记的位置。",
        "price": "MOP 46 · 模拟售价",
    },
]


class Command(BaseCommand):
    help = "Load dining and cultural-product examples without overwriting admin edits."

    @transaction.atomic
    def handle(self, *args, **options):
        added = 0
        for item in LISTINGS:
            defaults = {key: value for key, value in item.items() if key != "slug"}
            _, created = LocalListing.objects.get_or_create(slug=item["slug"], defaults=defaults)
            added += created
        self.stdout.write(self.style.SUCCESS(f"Discovery items added: {added}."))
