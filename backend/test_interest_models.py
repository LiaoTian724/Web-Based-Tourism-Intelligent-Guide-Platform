from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .forms import AttractionAdminForm, PlanForm, ProfileAdminForm, RegistrationForm
from .interests import InterestTag, validate_interest_tags
from .models import Attraction, Category, LocalListing, Profile, UserInteraction


class InterestModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="interest-test")
        cls.attraction = Attraction.objects.create(
            slug="history-sight", name="历史景点", category=Category.HISTORY,
            summary="简介", history="历史", address="澳门", hours="全天",
            admission="免费", latitude="22.19", longitude="113.54",
        )
        cls.listing = LocalListing.objects.create(
            slug="history-product", kind="product", name="历史主题纪念品",
            summary="简介", label="文创",
        )

    def test_vocabulary_is_independent_from_itinerary_categories(self):
        self.assertEqual(len(InterestTag.values), 15)
        self.assertEqual(Category.values, ["history", "culture", "photography", "food"])
        self.assertEqual(list(dict(RegistrationForm.base_fields["interests"].choices)), InterestTag.values)
        self.assertEqual(list(dict(PlanForm.base_fields["interests"].choices)), Category.values)
        self.assertTrue(PlanForm({"interests": ["food"], "budget_minutes": 60}).is_valid())
        self.assertFalse(PlanForm({"interests": ["souvenir"], "budget_minutes": 60}).is_valid())

    def test_multiple_cross_category_tags_round_trip(self):
        for obj in (self.attraction, self.listing):
            obj.tags = ["history", "souvenir", "design"]
            obj.full_clean()
            obj.save()
            obj.refresh_from_db()
            self.assertEqual(obj.tags, ["history", "souvenir", "design"])
        response = self.client.get(reverse("attractions"))
        item = response.json()["items"][0]
        self.assertEqual(item["tags"], ["history", "souvenir", "design"])
        self.assertEqual(item["tag_labels"], ["历史建筑", "纪念品", "艺术设计"])

    def test_invalid_json_unknown_and_duplicate_tags_are_rejected(self):
        for value in ({}, "", None, "history", ["food"], ["history", "history"], [1], [{}]):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    validate_interest_tags(value)
                for obj in (self.attraction, self.listing):
                    obj.tags = value
                    with self.assertRaises(ValidationError) as error:
                        obj.full_clean()
                    self.assertIn("tags", error.exception.message_dict)

    def test_empty_and_separate_default_lists_are_supported(self):
        first, second = Attraction(), Attraction()
        first.tags.append("history")
        self.assertEqual(second.tags, [])
        for obj in (self.attraction, self.listing):
            obj.tags = []
            obj.full_clean()

    def test_registration_persists_new_interests(self):
        response = self.client.post(reverse("register"), {
            "first_name": "测试旅客", "email": "new-interests@example.test",
            "password1": "Walking-Macau!34802", "password2": "Walking-Macau!34802",
            "interests": ["museum", "cafe_dessert", "handicraft"],
        })
        self.assertEqual(response.status_code, 302)
        profile = Profile.objects.get(user__username="new-interests@example.test")
        self.assertEqual(profile.interests, ["museum", "cafe_dessert", "handicraft"])
        self.assertFalse(UserInteraction.objects.exists())

    def test_registration_rejects_unknown_tags(self):
        form = RegistrationForm({
            "first_name": "测试旅客", "email": "invalid-interest@example.test",
            "password1": "Walking-Macau!34802", "password2": "Walking-Macau!34802",
            "interests": ["not-a-tag"],
        })
        self.assertFalse(form.is_valid())
        self.assertIn("interests", form.errors)

    def test_admin_uses_multiselect_and_preserves_legacy_preferences(self):
        self.assertEqual(list(dict(AttractionAdminForm.base_fields["tags"].choices)), InterestTag.values)
        profile = Profile.objects.create(user=self.user, interests=["food", "history"])
        form = ProfileAdminForm({"user": self.user.pk, "interests": ["food", "history"]}, instance=profile)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        profile.refresh_from_db()
        self.assertEqual(profile.interests, ["food", "history"])

    def test_interaction_database_rejects_missing_double_targets_or_unknown_action(self):
        invalid = [
            {"action": "view"},
            {"action": "view", "attraction": self.attraction, "listing": self.listing},
            {"action": "invented", "attraction": self.attraction},
        ]
        for fields in invalid:
            with self.subTest(fields=fields):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    UserInteraction.objects.create(user=self.user, **fields)

    def test_admin_cannot_manufacture_or_edit_interaction_events(self):
        request = RequestFactory().get("/admin/")
        request.user = self.user
        model_admin = admin.site._registry[UserInteraction]
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request))
