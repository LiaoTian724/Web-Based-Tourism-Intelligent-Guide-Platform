import json
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .interests import InterestTag
from .models import (
    Attraction,
    Bookmark,
    Category,
    InteractionAction,
    LocalListing,
    UserInteraction,
)


class InteractionFixtures(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="interaction-owner")
        cls.other_user = User.objects.create_user(username="other-visitor")
        cls.attraction = Attraction.objects.create(
            slug="interaction-attraction",
            name="测试景点",
            category=Category.HISTORY,
            summary="测试景点简介",
            history="测试历史",
            address="澳门",
            hours="全天",
            admission="免费",
            latitude="22.190000",
            longitude="113.540000",
        )
        cls.listing = LocalListing.objects.create(
            kind="food",
            slug="interaction-listing",
            name="测试餐厅",
            summary="测试餐厅简介",
            label="地道小吃",
            tags=[InterestTag.values[0]],
        )

    def setUp(self):
        self.client.force_login(self.user)


class ViewInteractionTests(InteractionFixtures):
    def post_view(self, **overrides):
        payload = {
            "target_type": "attraction",
            "target_id": self.attraction.pk,
            "action": "view",
        }
        payload.update(overrides)
        return self.client.post(reverse("user-interaction"), payload, content_type="application/json")

    def test_records_attraction_view_for_the_session_user(self):
        response = self.post_view()
        self.assertEqual(response.status_code, 201)
        interaction = UserInteraction.objects.get()
        self.assertEqual(response.json(), {"recorded": True, "id": interaction.pk})
        self.assertEqual(interaction.user, self.user)
        self.assertEqual(interaction.attraction, self.attraction)
        self.assertIsNone(interaction.listing_id)
        self.assertIsNone(interaction.impression_id)
        self.assertEqual(interaction.action, InteractionAction.VIEW)

    def test_records_listing_view_with_optional_impression_id(self):
        impression_id = uuid4()
        response = self.post_view(
            target_type="listing",
            target_id=self.listing.pk,
            impression_id=str(impression_id),
        )
        self.assertEqual(response.status_code, 201)
        interaction = UserInteraction.objects.get()
        self.assertEqual(interaction.listing, self.listing)
        self.assertIsNone(interaction.attraction_id)
        self.assertEqual(interaction.impression_id, impression_id)

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.post_view().status_code, 401)
        self.assertFalse(UserInteraction.objects.exists())

    def test_rejects_non_post_methods(self):
        for method in ("GET", "PUT", "PATCH", "DELETE"):
            with self.subTest(method=method):
                response = self.client.generic(method, reverse("user-interaction"))
                self.assertEqual(response.status_code, 405)
        self.assertFalse(UserInteraction.objects.exists())

    def test_rejects_malformed_json_and_non_object_payloads(self):
        for body in ("{", "", "[]", "null", "42", '"view"'):
            with self.subTest(body=body):
                response = self.client.post(
                    reverse("user-interaction"), body, content_type="application/json"
                )
                self.assertEqual(response.status_code, 400)
        response = self.client.post(
            reverse("user-interaction"),
            json.dumps({"target_type": "attraction", "target_id": self.attraction.pk, "action": "view"}),
            content_type="text/plain",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(UserInteraction.objects.exists())

    def test_rejects_missing_fields(self):
        valid = {"target_type": "attraction", "target_id": self.attraction.pk, "action": "view"}
        for missing in valid:
            with self.subTest(missing=missing):
                response = self.client.post(
                    reverse("user-interaction"),
                    {key: value for key, value in valid.items() if key != missing},
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 400)
        self.assertFalse(UserInteraction.objects.exists())

    def test_rejects_invalid_values_and_client_controlled_identity(self):
        cases = [
            {"target_id": value} for value in (0, -1, True, "1", 1.0, None, [], {})
        ] + [
            {"target_type": value} for value in ("user", "", None, [], {})
        ] + [
            {"action": value} for value in ("bookmark", "unbookmark", "click", None, [])
        ] + [
            {"impression_id": value} for value in ("not-a-uuid", "", None, 42, [])
        ] + [
            {"user": self.other_user.pk},
            {"user_id": self.other_user.pk},
            {"created_at": "2000-01-01T00:00:00Z"},
        ]
        for overrides in cases:
            with self.subTest(overrides=overrides):
                self.assertEqual(self.post_view(**overrides).status_code, 400)
        self.assertFalse(UserInteraction.objects.exists())

    def test_missing_and_disabled_targets_are_not_recorded(self):
        for target_type, target in (("attraction", self.attraction), ("listing", self.listing)):
            with self.subTest(target_type=target_type):
                self.assertEqual(
                    self.post_view(target_type=target_type, target_id=target.pk + 1000).status_code,
                    404,
                )
                target.enabled = False
                target.save(update_fields=["enabled"])
                self.assertEqual(
                    self.post_view(target_type=target_type, target_id=target.pk).status_code,
                    404,
                )
        self.assertFalse(UserInteraction.objects.exists())

    def test_separate_sessions_record_their_own_users(self):
        self.post_view()
        self.client.force_login(self.other_user)
        self.post_view()
        self.assertCountEqual(
            UserInteraction.objects.values_list("user_id", flat=True),
            [self.user.pk, self.other_user.pk],
        )

    def test_csrf_token_is_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        client.get(reverse("account"))
        payload = {"target_type": "attraction", "target_id": self.attraction.pk, "action": "view"}
        url = reverse("user-interaction")
        self.assertEqual(client.post(url, payload, content_type="application/json").status_code, 403)
        self.assertFalse(UserInteraction.objects.exists())
        response = client.post(
            url,
            payload,
            content_type="application/json",
            HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(UserInteraction.objects.count(), 1)

    def test_catalogue_reads_do_not_record_views(self):
        self.assertEqual(self.client.get(reverse("attractions")).status_code, 200)
        response = self.client.get(reverse("listings"))
        self.assertEqual(response.status_code, 200)
        item = response.json()["items"][0]
        self.assertEqual(item["tags"], self.listing.tags)
        self.assertEqual(item["tag_labels"], [InterestTag(self.listing.tags[0]).label])
        self.assertFalse(UserInteraction.objects.exists())


class BookmarkInteractionTests(InteractionFixtures):
    def bookmark_url(self):
        return reverse("listing-bookmark", args=[self.listing.pk])

    def test_only_state_changes_create_bookmark_events(self):
        url = self.bookmark_url()
        operations = [
            ("delete", False, 0),
            ("post", True, 1),
            ("post", True, 1),
            ("delete", False, 2),
            ("delete", False, 2),
            ("post", True, 3),
        ]
        for method, bookmarked, event_count in operations:
            with self.subTest(method=method, event_count=event_count):
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"bookmarked": bookmarked})
                self.assertEqual(Bookmark.objects.filter(user=self.user, listing=self.listing).exists(), bookmarked)
                self.assertEqual(UserInteraction.objects.count(), event_count)
        self.assertEqual(
            list(UserInteraction.objects.order_by("pk").values_list("action", flat=True)),
            [InteractionAction.BOOKMARK, InteractionAction.UNBOOKMARK, InteractionAction.BOOKMARK],
        )
        for interaction in UserInteraction.objects.all():
            self.assertEqual(interaction.user, self.user)
            self.assertEqual(interaction.listing, self.listing)
            self.assertIsNone(interaction.attraction_id)
            self.assertIsNone(interaction.impression_id)

    def test_cannot_change_another_users_bookmark(self):
        Bookmark.objects.create(user=self.other_user, listing=self.listing)
        response = self.client.delete(self.bookmark_url())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Bookmark.objects.filter(user=self.other_user, listing=self.listing).exists())
        self.assertFalse(UserInteraction.objects.exists())

    def test_unauthenticated_and_disabled_targets_create_no_events(self):
        self.client.logout()
        for method in ("post", "delete"):
            self.assertEqual(getattr(self.client, method)(self.bookmark_url()).status_code, 401)
        self.client.force_login(self.user)
        self.listing.enabled = False
        self.listing.save(update_fields=["enabled"])
        for method in ("post", "delete"):
            self.assertEqual(getattr(self.client, method)(self.bookmark_url()).status_code, 404)
        self.assertFalse(Bookmark.objects.exists())
        self.assertFalse(UserInteraction.objects.exists())

    def test_bookmark_creation_rolls_back_if_event_recording_fails(self):
        with patch("backend.community.UserInteraction.objects.create", side_effect=RuntimeError("recording failed")):
            with self.assertRaises(RuntimeError):
                self.client.post(self.bookmark_url())
        self.assertFalse(Bookmark.objects.exists())
        self.assertFalse(UserInteraction.objects.exists())

    def test_bookmark_deletion_rolls_back_if_event_recording_fails(self):
        bookmark = Bookmark.objects.create(user=self.user, listing=self.listing)
        with patch("backend.community.UserInteraction.objects.create", side_effect=RuntimeError("recording failed")):
            with self.assertRaises(RuntimeError):
                self.client.delete(self.bookmark_url())
        self.assertTrue(Bookmark.objects.filter(pk=bookmark.pk).exists())
        self.assertFalse(UserInteraction.objects.exists())

    def test_bookmark_endpoint_retains_csrf_protection(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        for method in ("post", "delete"):
            self.assertEqual(getattr(client, method)(self.bookmark_url()).status_code, 403)
        self.assertFalse(Bookmark.objects.exists())
        self.assertFalse(UserInteraction.objects.exists())
