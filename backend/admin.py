from django.contrib import admin

from .models import (
    AIItineraryDraft,
    Attraction,
    Bookmark,
    GuideExchange,
    GuideSession,
    Itinerary,
    ItineraryStop,
    LocalListing,
    Profile,
    Review,
    ReviewNotification,
)


admin.site.site_header = "澳門漫遊 · 内容管理"
admin.site.site_title = "澳門漫遊后台"
admin.site.index_title = "旅游平台数据管理"


@admin.register(Attraction)
class AttractionAdmin(admin.ModelAdmin):
    list_display = ("name", "region", "sight_type", "world_heritage", "enabled")
    list_filter = ("region", "sight_type", "world_heritage", "category", "less_known", "enabled")
    search_fields = ("name", "name_en", "address")
    list_editable = ("enabled",)
    prepopulated_fields = {"slug": ("name_en",)}


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user",)
    search_fields = ("user__username",)


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "budget_minutes", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username",)


@admin.register(ItineraryStop)
class ItineraryStopAdmin(admin.ModelAdmin):
    list_display = ("itinerary", "attraction", "position", "walk_minutes", "visit_minutes")
    list_filter = ("attraction__region",)
    search_fields = ("attraction__name", "itinerary__user__username")


@admin.register(LocalListing)
class LocalListingAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "area", "food_group", "enabled")
    list_filter = ("kind", "food_group", "area", "enabled")
    search_fields = ("name", "address", "label")
    list_editable = ("enabled",)


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "listing")
    search_fields = ("user__username", "listing__name")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "attraction", "listing", "rating", "status", "updated_at")
    list_filter = ("status", "rating", "updated_at")
    search_fields = ("body", "user__username", "attraction__name", "listing__name")


@admin.register(ReviewNotification)
class ReviewNotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "target_name", "status", "created_at", "read_at")
    list_filter = ("status", "created_at", "read_at")
    search_fields = ("user__username", "target_name")


@admin.register(GuideSession)
class GuideSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "updated_at")
    search_fields = ("user__username", "title")


@admin.register(GuideExchange)
class GuideExchangeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session", "created_at")
    search_fields = ("user__username", "question", "answer")
    readonly_fields = ("created_at",)


@admin.register(AIItineraryDraft)
class AIItineraryDraftAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "budget_minutes", "created_at")
    search_fields = ("user__username", "request_text")
    readonly_fields = ("created_at",)
