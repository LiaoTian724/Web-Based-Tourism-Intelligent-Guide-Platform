from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Category


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(label="称呼", max_length=100)

    email = forms.EmailField(label="邮箱", max_length=150)

    interests = forms.MultipleChoiceField(
        label="感兴趣的内容",
        choices=Category.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "email", "interests")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("该邮箱已经注册。")

        return email

    def clean(self):
        cleaned = super().clean()

        if cleaned.get("email"):
            self.instance.username = cleaned["email"]

        return cleaned


# class LoginForm(AuthenticationForm):
#     username = forms.CharField(label="邮箱或管理员账号", max_length=150)

#     def clean_username(self):
#         username = self.cleaned_data["username"].strip()

#         if "@" in username:
#             username = username.lower()

#         return username





class LoginForm(AuthenticationForm):
    username = forms.CharField(label="邮箱或管理员账号", max_length=150)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        # 如果输入的是邮箱，查询对应的用户名
        if "@" in username:
            users = User.objects.filter(email__iexact=username).values_list("username", flat=True)[:2]
            users = list(users)

            # 找到唯一的用户
            if len(users) == 1:
                return users[0]

            # 一个邮箱对应多个账号
            if len(users) > 1:
                raise ValidationError("该邮箱对应多个账号，请使用用户名登录。")

        # 如果不是邮箱，直接使用用户名登录
        return username






class PlanForm(forms.Form):
    interests = forms.MultipleChoiceField(
        choices=Category.choices, required=False,
    )

    budget_minutes = forms.IntegerField(
        min_value=30, max_value=480,
    )
