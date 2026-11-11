from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

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


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="邮箱或管理员账号", max_length=150)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        if "@" in username:
            username = username.lower()

        return username
