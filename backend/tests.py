from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import (Attraction, Category, LocalListing, Region, Review, ReviewStatus, SightType,)


class ListingReviewTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.user1 = User.objects.create_user(username="user1", password="test123456")
        self.user2 = User.objects.create_user(username="user2", password="test123456")
        self.listing = LocalListing.objects.create(
            kind="food",
            slug="test-food",
            name="测试美食",
            summary="测试用美食",
            label="地道小吃",
        )

    def test_only_approved_reviews_are_public(self):
        # 创建审核通过的评价
        Review.objects.create(
            user=self.user1,
            listing=self.listing,
            rating=5,
            body="很好吃",
            status=ReviewStatus.APPROVED,
        )

        # 创建待审核的评价
        Review.objects.create(
            user=self.user2,
            listing=self.listing,
            rating=3,
            body="一般般",
            status=ReviewStatus.PENDING,
        )

        # 模拟向 Django 发送 GET 请求
        url = reverse("listing-reviews", args=[self.listing.id])
        response = self.client.get(url)

        # 检查 HTTP 状态码
        self.assertEqual(response.status_code, 200)

        # 读取 API 返回的 JSON
        data = response.json()
        # 应该只有一条公开评价
        self.assertEqual(len(data["items"]), 1)

        # 公开评价应该属于 user1
        self.assertEqual(data["items"][0]["body"], "很好吃")




class AttractionFilterTests(TestCase):
    def create_attraction(self, slug, name, **extra):
        data = {
            "slug": slug,
            "name": name,
            "category": Category.HISTORY,
            "summary": "测试景点简介",
            "history": "测试景点历史",
            "address": name + "附近",
            "hours": "09:00-18:00",
            "admission": "免费",
            "latitude": "22.190000",
            "longitude": "113.540000",
        }
        data.update(extra)
        return Attraction.objects.create(**data)

    def setUp(self):
        self.create_attraction(
            "a-ma-temple",
            "妈阁庙",
            category=Category.CULTURE,
            sight_type=SightType.TEMPLES,
            world_heritage=True,
            region=Region.PENINSULA,
        )

        self.create_attraction(
            "mandarins-house",
            "郑家大屋",
            sight_type=SightType.MUSEUMS,
            world_heritage=True,
            region=Region.PENINSULA,
            less_known=True,
        )

        self.create_attraction(
            "taipa-church",
            "氹仔教堂",
            sight_type=SightType.CHURCHES,
            region=Region.TAIPA,
            less_known=True,
        )

        self.create_attraction(
            "unknown-place",
            "未分类景点",
            sight_type="",
            world_heritage=False,
            less_known=True,
        )

        self.create_attraction(
            "heritage-square",
            "历史广场",
            sight_type="",
            world_heritage=True,
        )

    def get_names(self, **params):
        response = self.client.get(reverse("attractions"), params)
        self.assertEqual(response.status_code, 200)

        return {item["name"] for item in response.json()["items"]}

    def test_heritage_filter(self):
        self.assertSetEqual(self.get_names(theme="heritage"), {"妈阁庙", "郑家大屋", "历史广场"})

    def test_sight_type_filter(self):
        self.assertSetEqual(self.get_names(theme="temples"), {"妈阁庙"})

    def test_other_filter(self):
        self.assertSetEqual(self.get_names(theme="other"), {"未分类景点"})


    def test_combined_filters(self):
        self.assertSetEqual(
            self.get_names(q="郑家", category=Category.HISTORY, region=Region.PENINSULA, theme="museums", less_known="1",),
            {"郑家大屋"}
        )

    def test_export_uses_same_filters(self):
        response = self.client.get(
            reverse("export-attractions"),
            {
                "theme": "museums",
                "region": Region.PENINSULA,
                "less_known": "1",
            }
        )

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("郑家大屋", content)
        self.assertNotIn("妈阁庙", content)