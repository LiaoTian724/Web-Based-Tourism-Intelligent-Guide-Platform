from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import community, views, accounts
from .forms import LoginForm

urlpatterns = [
    path("api/healthz/", views.healthz, name="healthz"),

    path("api/attractions/", views.attractions, name="attractions"),

    path("api/listings/", community.listings, name="listings"),
    path("api/listings/<int:listing_id>/reviews/", community.listing_reviews, name="listing-reviews",),
    path("api/listings/<int:listing_id>/bookmark/", community.listing_bookmark, name="listing-bookmark",),

    path("api/account/", accounts.current_account, name="account"),

    path("accounts/register/", accounts.register, name="register"),
    path("accounts/login/",
          LoginView.as_view(template_name="account.html", authentication_form=LoginForm, success_url_allowed_hosts={"127.0.0.1:5173"},),
          name="login",
    ),
    path("accounts/logout/",
          LogoutView.as_view(next_page="http://127.0.0.1:5173/", success_url_allowed_hosts={"127.0.0.1:5173"},),
          name="logout",
    ),

    path("api/bookmarks/", community.my_bookmarks, name="my-bookmarks"),

    path("api/itineraries/plan/", views.plan, name="plan",),
    path("api/itineraries/", views.itineraries, name="itineraries",),
    path("api/itineraries/<int:pk>/export/", views.export_itinerary, name="export-itinerary",),
]
