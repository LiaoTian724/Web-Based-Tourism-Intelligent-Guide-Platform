from django.urls import path

from . import community, views

urlpatterns = [
    path("api/healthz/", views.healthz, name="healthz"),
    path("api/attractions/", views.attractions, name="attractions"),
    path("api/listings/", community.listings, name="listings"),
]
