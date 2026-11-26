"""Load the three documented Macao attraction examples."""

from django.core.management.base import BaseCommand
from django.db import transaction

from backend.models import Attraction


TOURISM = "https://www.macaotourism.gov.mo/en/"
PLACES = [
    {
        "slug": "ruins-of-st-pauls", "artwork": "ruins",
        "name": "大三巴牌坊", "name_en": "Ruins of St. Paul’s", "category": "history",
        "summary": "沿石阶走近澳门最具辨识度的教堂立面，读一段澳门的中西交流史。",
        "history": "这里原是圣保禄学院相邻的天主之母教堂。教堂毁于 1835 年大火，留存的正面石墙如今是澳门历史城区的一部分。",
        "address": "澳门耶稣会纪念广场", "hours": "09:00–18:00，17:30 停止入场。请以官方公告为准。",
        "admission": "牌坊外观免费参观", "visit_minutes": 35,
        "latitude": "22.197500", "longitude": "113.540830",
        "source_url": TOURISM + "sightseeing/macao-world-heritage/ruins-of-st-pauls",
    },
    {
        "slug": "senado-square", "artwork": "senado",
        "name": "议事亭前地", "name_en": "Senado Square", "category": "photography",
        "summary": "波浪石砖、浅色建筑和街巷在这里交汇，从广场出发漫步旧城。",
        "history": "议事亭前地长期是澳门市中心的重要公共空间。广场连接市政署大楼、仁慈堂及周边传统街区，是认识历史城区城市生活的一站。",
        "address": "澳门议事亭前地", "hours": "室外广场，周边场馆开放时间各异。",
        "admission": "免费", "visit_minutes": 25,
        "latitude": "22.193670", "longitude": "113.539700",
        "source_url": TOURISM + "step-out-macao/central/senado-square",
    },
    {
        "slug": "a-ma-temple", "artwork": "ama",
        "name": "妈阁庙", "name_en": "A-Ma Temple", "category": "culture",
        "summary": "从妈阁前地走进依山而建的庙宇，认识澳门的海洋信仰。",
        "history": "妈阁庙由依山分布的殿阁组成，供奉妈祖及其他神祇，展现澳门沿岸居民的多元传统信仰。",
        "address": "澳门妈阁前地", "hours": "请查看官方开放信息及现场公告。",
        "admission": "免费", "visit_minutes": 30,
        "latitude": "22.186110", "longitude": "113.531510",
        "source_url": TOURISM + "sightseeing/macao-world-heritage/a-ma-temple",
    },
]


class Command(BaseCommand):
    help = "Create the demo attractions, preserving subsequent admin edits."

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        for item in PLACES:
            defaults = {key: value for key, value in item.items() if key != "slug"}
            _, was_created = Attraction.objects.get_or_create(slug=item["slug"], defaults=defaults)
            created += was_created
        self.stdout.write(self.style.SUCCESS(f"Demo attractions added: {created}."))
