from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import LocalListing, Review, ReviewStatus


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
