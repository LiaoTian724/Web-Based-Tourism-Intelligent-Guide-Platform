from django.urls import path

from . import views

urlpatterns = [
    path("api/healthz/", views.healthz, name="healthz"),
    path("api/attractions/", views.attractions, name="attractions"),
]
