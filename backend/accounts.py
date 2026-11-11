from django.contrib.auth import login
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from .forms import RegistrationForm
from .models import Profile

FRONTEND_URL = "http://127.0.0.1:5173/"


def get_frontend_url(request):
    target = request.POST.get("next") or request.GET.get("next")

    allowed_hosts = {request.get_host(), "127.0.0.1:5173"}

    if target and url_has_allowed_host_and_scheme(target, allowed_hosts, require_https=request.is_secure()):
        return target

    return FRONTEND_URL


@require_http_methods(["GET", "POST"])
def register(request):
    target = get_frontend_url(request)

    if request.user.is_authenticated:
        return redirect(target)

    form = RegistrationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save()

                Profile.objects.create(user=user, interests=form.cleaned_data["interests"])

        except IntegrityError:
            form.add_error("email", "该邮箱已经注册。")

        else:
            login(request, user)
            return redirect(target)

    return render(request, "account.html", {"form": form, "register": True, "next": target})


@ensure_csrf_cookie
@require_GET
def current_account(request):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse({"authenticated": False, "account": None, "staff": False})

    return JsonResponse(
        {
            "authenticated": True,
            "account": user.first_name.strip() or user.username,
            "staff": user.is_staff,
        }
    )
