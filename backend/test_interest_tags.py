from io import StringIO

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from .interests import InterestTag, validate_interest_tags
from .models import Attraction, Category, ListingKind, LocalListing, SightType
from .tagging import suggest_attraction_tags, suggest_listing_tags


class InterestTagSuggestionTests(SimpleTestCase):
    def test_ruins_have_multiple_relevant_interests(self):
        place = Attraction(
            slug="ruins-of-st-pauls", name="大三巴牌坊", category=Category.HISTORY,
            sight_type=SightType.CHURCHES, world_heritage=True,
        )
        self.assertEqual(suggest_attraction_tags(place), ["history", "culture", "photography", "religion"])

    def test_portuguese_tart_is_a_snack_and_dessert(self):
        item = LocalListing(kind=ListingKind.FOOD, name="葡式蛋挞", label="葡挞与烘焙")
        self.assertEqual(suggest_listing_tags(item), ["local_snacks", "cafe_dessert"])

    def test_landmark_souvenir_can_cross_interest_categories(self):
        # This is a test fixture, not an addition to the real catalogue.
        item = LocalListing(kind=ListingKind.PRODUCT, name="大三巴主题冰箱贴")
        self.assertEqual(suggest_listing_tags(item), ["history", "souvenir", "design"])

    def test_broad_food_groups_do_not_imply_a_specific_interest(self):
        for group in ("snacks", "specialty", "cafes"):
            with self.subTest(group=group):
                item = LocalListing(kind=ListingKind.FOOD, name="测试餐厅", food_group=group)
                self.assertEqual(suggest_listing_tags(item), [])

    def test_noodles_are_not_automatically_cafe_dessert(self):
        item = LocalListing(kind=ListingKind.FOOD, name="六记粥面", label="粥面", food_group="cafes")
        self.assertEqual(suggest_listing_tags(item), ["local_dining"])

    def test_workshop_name_does_not_imply_handicraft(self):
        item = LocalListing(kind=ListingKind.PRODUCT, name="森梦工坊", label="文创咖啡空间")
        self.assertEqual(suggest_listing_tags(item), ["cafe_dessert", "design"])

    def test_explicit_craft_description_is_recognized(self):
        item = LocalListing(kind=ListingKind.PRODUCT, name="示例店", summary="展示传统木雕与竹编手工艺。")
        self.assertEqual(suggest_listing_tags(item), ["handicraft"])

    def test_landmark_nearby_is_not_a_product_theme(self):
        item = LocalListing(kind=ListingKind.PRODUCT, name="示例礼品店", summary="位于大三巴附近，售卖生活用品。")
        self.assertEqual(suggest_listing_tags(item), ["souvenir"])

    def test_suggestions_use_only_unique_valid_vocabulary(self):
        self.assertEqual(len(InterestTag.values), 15)
        places = [
            Attraction(category=Category.CULTURE, sight_type=SightType.MUSEUMS, world_heritage=True, less_known=True),
            Attraction(category=Category.PHOTOGRAPHY, sight_type=SightType.PARKS, summary="适合漫步、休息和拍照。"),
        ]
        items = [
            LocalListing(kind=ListingKind.FOOD, name="葡国餐厅", label="葡式料理"),
            LocalListing(kind=ListingKind.PRODUCT, name="故宫博物馆文创礼品", summary="宗教主题的传统木雕设计。"),
        ]
        for tags in [*(suggest_attraction_tags(place) for place in places), *(suggest_listing_tags(item) for item in items)]:
            validate_interest_tags(tags)
            self.assertEqual(len(tags), len(set(tags)))
            self.assertTrue(set(tags).issubset(InterestTag.values))


class SeedInterestTagsTests(TestCase):
    def setUp(self):
        self.place = Attraction.objects.create(
            slug="ruins-of-st-pauls", name="大三巴牌坊", category=Category.HISTORY,
            sight_type=SightType.CHURCHES, world_heritage=True, summary="牌坊",
            history="历史", address="澳门", hours="室外", admission="免费",
            latitude="22.197500", longitude="113.540830",
        )
        self.tart = LocalListing.objects.create(
            kind=ListingKind.FOOD, slug="test-tart", name="葡式蛋挞", summary="葡挞与烘焙", label="甜品",
        )
        self.unknown = LocalListing.objects.create(
            kind=ListingKind.FOOD, slug="test-unknown", name="测试餐厅", summary="信息待补充", label="餐厅",
        )

    def test_dry_run_previews_without_saving(self):
        output = StringIO()
        call_command("seed_interest_tags", dry_run=True, stdout=output)
        self.place.refresh_from_db()
        self.tart.refresh_from_db()
        self.assertEqual(self.place.tags, [])
        self.assertEqual(self.tart.tags, [])
        self.assertIn("ruins-of-st-pauls: history, culture, photography, religion", output.getvalue())
        self.assertIn("remaining untagged 1", output.getvalue())

    def test_repeated_runs_preserve_manual_edits_and_unrelated_fields(self):
        self.tart.tags = ["souvenir"]
        self.tart.save(update_fields=["tags"])
        call_command("seed_interest_tags", stdout=StringIO())
        self.place.refresh_from_db()
        self.assertEqual(self.place.tags, ["history", "culture", "photography", "religion"])
        self.place.tags = ["photography"]
        self.place.save(update_fields=["tags"])
        call_command("seed_interest_tags", stdout=StringIO())
        self.place.refresh_from_db()
        self.tart.refresh_from_db()
        self.unknown.refresh_from_db()
        self.assertEqual(self.place.tags, ["photography"])
        self.assertEqual(self.tart.tags, ["souvenir"])
        self.assertEqual(self.unknown.tags, [])
        self.assertEqual(self.place.category, Category.HISTORY)
        self.assertEqual(self.place.summary, "牌坊")
