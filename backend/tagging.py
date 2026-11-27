"""Conservative catalogue tag suggestions from existing descriptive fields.

These rules describe places and products, not inferred user preferences. They
deliberately leave ambiguous records untagged so an editor can review them.
"""

from .interests import InterestTag, validate_interest_tags
from .models import Category, ListingKind, SightType


def _text(item, *fields):
    return " ".join(str(getattr(item, field, "") or "") for field in fields).casefold()


def _contains(text, words):
    return any(word in text for word in words)


def _ordered(tags):
    result = [tag.value for tag in InterestTag if tag in tags]
    validate_interest_tags(result)
    return result


def _food_tags(text):
    """Use explicit food descriptions, not a broad catalogue food group."""
    tags = set()
    if _contains(text, (
        "葡挞", "葡撻", "蛋挞", "蛋撻", "猪扒包", "豬扒包", "牛杂", "牛雜",
        "杏仁饼", "杏仁餅", "鸡仔饼", "雞仔餅", "凤凰卷", "鳳凰卷",
        "木糠布甸", "大菜糕", "传统饼食", "傳統餅食", "地道小吃", "澳门小吃", "澳門小吃",
    )):
        tags.add(InterestTag.LOCAL_SNACKS)
    if _contains(text, (
        "葡国菜", "葡國菜", "葡国餐", "葡國餐", "葡国料理", "葡國料理",
        "葡式料理", "葡式餐饮", "葡式餐飲", "葡式食品", "葡式辣鱼", "葡式辣魚",
        "澳葡料理", "澳葡餐", "土生菜", "土生葡菜",
    )):
        tags.add(InterestTag.PORTUGUESE_FOOD)
    if _contains(text, (
        "咖啡", "甜品", "甜点", "甜點", "蛋挞", "蛋撻", "葡挞", "葡撻",
        "雪糕", "冰淇淋", "蛋糕", "糕点", "糕點", "布甸", "布丁", "烘焙",
        "冰室", "café", "cafe", "coffee", "dessert",
    )):
        tags.add(InterestTag.CAFE_DESSERT)
    if _contains(text, (
        "街坊餐饮", "街坊餐飲", "茶餐厅", "茶餐廳", "茶餐室", "茶楼", "茶樓",
        "粥面", "粥麵", "粉面", "粉麵", "云吞", "雲吞", "虾籽捞面", "蝦籽撈麵",
        "水蟹粥", "地道餐馆", "地道餐館",
    )):
        tags.add(InterestTag.LOCAL_DINING)
    return tags


def suggest_attraction_tags(place):
    tags = set()
    category_tags = {
        Category.HISTORY: InterestTag.HISTORY,
        Category.CULTURE: InterestTag.CULTURE,
        Category.PHOTOGRAPHY: InterestTag.PHOTOGRAPHY,
    }
    if place.category in category_tags:
        tags.add(category_tags[place.category])
    if place.world_heritage:
        tags.update((InterestTag.HISTORY, InterestTag.CULTURE))
    if place.less_known:
        tags.add(InterestTag.HIDDEN_GEMS)
    if place.sight_type == SightType.MUSEUMS:
        tags.update((InterestTag.MUSEUM, InterestTag.CULTURE))
    elif place.sight_type in (SightType.CHURCHES, SightType.TEMPLES):
        tags.update((InterestTag.RELIGION, InterestTag.CULTURE))
    elif place.sight_type == SightType.PARKS:
        tags.update((InterestTag.NATURE, InterestTag.LEISURE))
    elif place.sight_type == SightType.FORTRESSES:
        tags.add(InterestTag.HISTORY)

    name = _text(place, "name", "name_en")
    description = _text(place, "name", "summary")
    if _contains(name, ("博物馆", "博物館", "展览厅", "展覽廳", "museum")):
        tags.add(InterestTag.MUSEUM)
    if _contains(description, ("摄影", "攝影", "拍照", "打卡")):
        tags.add(InterestTag.PHOTOGRAPHY)
    if _contains(description, ("漫步", "散步", "休闲", "休閒", "休息")):
        tags.add(InterestTag.LEISURE)
    if place.slug == "ruins-of-st-pauls" or "大三巴牌坊" in name:
        tags.update((InterestTag.HISTORY, InterestTag.CULTURE, InterestTag.PHOTOGRAPHY, InterestTag.RELIGION))
    if place.category == Category.FOOD:
        tags.update(_food_tags(description))
    return _ordered(tags)


def suggest_listing_tags(item):
    description = _text(item, "name", "label", "summary")
    tags = _food_tags(description)
    if item.kind == ListingKind.PRODUCT:
        if _contains(description, (
            "手信", "纪念", "紀念", "礼品", "禮品", "伴手礼", "伴手禮", "明信片",
            "冰箱贴", "冰箱貼", "集章册", "集章冊", "杯垫", "杯墊", "souvenir",
        )):
            tags.add(InterestTag.SOUVENIR)
        if _contains(description, ("设计", "設計", "原创", "原創", "文创", "文創", "纹样", "紋樣", "主题", "主題")):
            tags.add(InterestTag.DESIGN)

        # A workshop/shop name does not establish traditional craft content.
        craft_description = _text(item, "label", "summary")
        if _contains(craft_description, (
            "手工艺", "手工藝", "传统工艺", "傳統工藝", "非遗", "非遺", "手工作品",
            "木雕", "竹编", "竹編", "剪纸", "剪紙", "陶艺", "陶藝", "刺绣", "刺繡", "漆器",
        )):
            tags.add(InterestTag.HANDICRAFT)

        # Nearby landmarks in a shop description are not necessarily its theme.
        theme_text = _text(item, "name", "label")
        summary = _text(item, "summary")
        if _contains(summary, ("主题", "主題", "纹样", "紋樣", "灵感", "靈感", "图案", "圖案", "造型", "印有")):
            theme_text += " " + summary
        if _contains(theme_text, ("大三巴", "历史", "歷史", "世遗", "世遺", "郑家大屋", "鄭家大屋")):
            tags.add(InterestTag.HISTORY)
        if _contains(theme_text, ("博物馆", "博物館", "博物院", "艺博馆", "藝博館", "故宫", "故宮")):
            tags.add(InterestTag.MUSEUM)
        if _contains(theme_text, ("庙宇", "廟宇", "教堂", "圣堂", "聖堂", "妈祖", "媽祖", "宗教")):
            tags.add(InterestTag.RELIGION)
    return _ordered(tags)
