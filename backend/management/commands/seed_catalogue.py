"""Expand the editable catalogue with Macau tourism references."""

import json
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from backend.discovery_photos import PHOTO_CREDITS
from backend.models import Attraction, ListingKind, LocalListing, Region

MGTO = "https://www.macaotourism.gov.mo/en/"
HERITAGE = MGTO + "sightseeing/macao-world-heritage"
TAIPA = "https://content.macaotourism.gov.mo/uploads/mgto_brochures/1fc4deada16c963a3e5af06b04cfb2ef2e747646.pdf"
COFFEE = MGTO + "dining/specialty-foods/coffee-shops-and-noodle-shops"
OPEN_DINING = Path(__file__).resolve().parents[2] / "data" / "macau_open_dining.json"
CATALOGUE_DATA = Path(__file__).resolve().parents[2] / "data"

# Map pins are approximate access points. The descriptions paraphrase the sources.
SIGHTS = [
    ("mandarins-house", "郑家大屋", "Mandarin’s House", "history", Region.PENINSULA, True, "龙头左巷 10 号", "22.18758", "113.53446", 35, "在院落和灰砖墙之间看中西建筑细节。这里曾是郑观应的居所。", HERITAGE),
    ("lilau-square", "亚婆井前地", "Lilau Square", "culture", Region.PENINSULA, True, "亚婆井前地", "22.18778", "113.53421", 15, "在旧城的小广场停一停，这一带的泉水曾是澳门的重要水源。", HERITAGE + "/lilau-square"),
    ("lou-kau-mansion", "卢家大屋", "Lou Kau Mansion", "history", Region.PENINSULA, True, "大堂巷 7 号", "22.19425", "113.54069", 25, "闹市小巷里的灰砖宅院，可近看传统西关住宅的空间和细部。", MGTO + "sightseeing/museums-and-galleries/lou-kau-mansion"),
    ("st-dominics-church", "玫瑰堂", "St. Dominic’s Church", "history", Region.PENINSULA, False, "板樟堂前地", "22.19473", "113.54019", 25, "从广场走进历史城区的教堂群，留意淡黄色立面与附近的街巷。", HERITAGE),
    ("mount-fortress", "大炮台", "Mount Fortress", "photography", Region.PENINSULA, False, "澳门博物馆前地", "22.19741", "113.54173", 30, "从大三巴附近上山看炮台城墙与城市景观。", HERITAGE),
    ("guia-fortress", "东望洋炮台与灯塔", "Guia Fortress and Lighthouse", "photography", Region.PENINSULA, False, "东望洋山", "22.19648", "113.54954", 40, "在山顶看炮台、圣堂和灯塔，适合留出时间慢慢步行。", MGTO + "macao-full-of-fun/art-and-cultural-tour-in-st-lazarus-parish/guia-fortress-including-guia-chapel-and-lighthouse"),
    ("lou-lim-ioc-garden", "卢廉若公园", "Lou Lim Ioc Garden", "culture", Region.PENINSULA, True, "罗利老马路 10 号", "22.20048", "113.54879", 30, "池塘、曲桥和亭榭组成适合休息的中式园林。", MGTO + "step-out-macao/st-lazarus-parish/lou-lim-ioc-garden"),
    ("dom-pedro-v-theatre", "岗顶剧院", "Dom Pedro V Theatre", "culture", Region.PENINSULA, True, "岗顶前地", "22.19195", "113.53758", 25, "在岗顶前地看西式剧院建筑，周边还有圣堂与图书馆。", HERITAGE),
    ("taipa-houses", "龙环葡韵", "Taipa Houses", "photography", Region.TAIPA, False, "氹仔海边马路", "22.15280", "113.56108", 35, "沿湖漫步，看葡式住宅群的立面与氹仔旧城风貌。", TAIPA),
    ("iec-long", "益隆炮竹厂旧址", "Former Iec Long Firecracker Factory", "culture", Region.TAIPA, True, "氹仔飞能便度街", "22.15432", "113.55932", 35, "看旧厂的水道与生产空间，了解澳门炮竹制造业的历史。", TAIPA),
    ("rua-do-cunha", "官也街", "Rua do Cunha", "food", Region.TAIPA, False, "氹仔官也街", "22.15342", "113.55773", 25, "在氹仔旧城区的一条短街上找小吃和手信。", TAIPA),
    ("st-francis-xavier-coloane", "路环圣方济各圣堂", "Chapel of St. Francis Xavier", "culture", Region.COLOANE, True, "路环马忌士前地", "22.11706", "113.55141", 25, "在路环村的广场与海边之间看这座小教堂。", MGTO + "sightseeing/churches/chapel-of-st-francis-xavier"),
]

NEW_LISTINGS = [
    dict(slug="ngao-kei", kind="food", name="牛记咖喱美食", label="咖喱与面食", area=Region.PENINSULA,
         address="澳门十月初五日街一带", summary="在内港旧街一带寻找咖喱、粥面等澳门街坊餐饮。", latitude=22.19541, longitude=113.53706,
         source_url=MGTO + "step-out-macao/central/estabelecimento-de-comidas-ngao-kei-ka-lei", image_key="curry"),
    dict(slug="tai-lei-loi-kei", kind="food", name="大利来记", label="猪扒包", area=Region.TAIPA,
         address="澳门氹仔旧城区，导航前请确认分店", summary="适合作为氹仔旧城行程中的小吃一站。", latitude=22.15343, longitude=113.55774,
         source_url=COFFEE, image_key="bun"),
    dict(slug="nam-ping", kind="food", name="南屏雅叙", label="茶餐室", area=Region.PENINSULA,
         address="澳门十月初五日街 85–85A 号", summary="沿十月初五街散步时可留意这家旧式茶餐室。", latitude=22.19591, longitude=113.53742,
         source_url=COFFEE, image_key="coffee"),
    dict(slug="macao-tile-coaster", kind="product", name="澳门花砖杯垫", label="澳門漫遊课程设计", area=Region.TAIPA,
         summary="以蓝白葡砖的几何纹样设计的一枚杯垫。文创陈列样例。", price="MOP 36 · 模拟售价", image_key="tile"),
]

METADATA = {
    "wong-chi-kei-senado": ("noodles", "https://images.io.gov.mo/bo/ii/2021/17/avisosoficiais-17-2021.pdf"),
    "margarets-cafe-e-nata": ("tart", "https://www.mlocal.biz/biz/4e6536077aaa91367f000e6e"),
    "a-lorcha": ("meal", "https://alorcha.com/en/contact/"),
    "azulejo-postcards": ("postcards", ""),
    "heritage-stamp-book": ("stamp", ""),
}


class Command(BaseCommand):
    help = "Load additional Macau sights and discovery listings. Existing edits are preserved."

    @transaction.atomic
    def handle(self, *args, **options):
        existing_sights = set(Attraction.objects.values_list("slug", flat=True))
        existing_listings = set(LocalListing.objects.values_list("slug", flat=True))
        call_command("seed_demo")
        call_command("seed_discovery")
        for slug, name, name_en, category, region, less_known, address, lat, lng, minutes, summary, source in SIGHTS:
            artwork = "taipa" if slug == "taipa-houses" else slug
            Attraction.objects.get_or_create(slug=slug, defaults={
                "name": name, "name_en": name_en, "category": category, "region": region,
                "less_known": less_known, "address": address, "latitude": lat, "longitude": lng,
                "visit_minutes": minutes, "summary": summary, "history": summary,
                "hours": "出发前请查看官方开放信息。", "admission": "请查看官方或现场公告。",
                "source_url": source, "artwork": artwork,
            })
            Attraction.objects.filter(slug=slug, artwork="").update(artwork=artwork)
        for row in NEW_LISTINGS:
            LocalListing.objects.get_or_create(slug=row["slug"], defaults={k: v for k, v in row.items() if k != "slug"})
        for row in json.loads(OPEN_DINING.read_text(encoding="utf-8"))["listings"]:
            slug = row["slug"]
            defaults = {key: value for key, value in row.items() if key not in ("slug", "osm_url")}
            LocalListing.objects.get_or_create(slug=slug, defaults={"kind": ListingKind.FOOD, **defaults})
            if slug in PHOTO_CREDITS:
                LocalListing.objects.filter(slug=slug, image_key="").update(image_key=slug)
        for slug, (image, source) in METADATA.items():
            LocalListing.objects.filter(slug=slug, image_key="").update(image_key=image)
            if source:
                LocalListing.objects.filter(slug=slug, source_url="").update(source_url=source)
        call_command(
            "seed_topics",
            sight_slugs=sorted(set(Attraction.objects.values_list("slug", flat=True)) - existing_sights),
            food_slugs=sorted(set(LocalListing.objects.values_list("slug", flat=True)) - existing_listings),
        )
        for model, filename in (
            (Attraction, "expanded_attractions.json"),
            (LocalListing, "expanded_local_listings.json"),
        ):
            field_names = {field.name for field in model._meta.fields} - {"id", "slug"}
            for row in json.loads((CATALOGUE_DATA / filename).read_text(encoding="utf-8")):
                defaults = {key: value for key, value in row.items() if key in field_names}
                model.objects.get_or_create(slug=row["slug"], defaults=defaults)
        self.stdout.write(self.style.SUCCESS(f"{Attraction.objects.filter(enabled=True).count()} attractions, {LocalListing.objects.filter(enabled=True).count()} listings available."))
