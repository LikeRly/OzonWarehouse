from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

# Регистрация пользователя (кастомная форма)
class CustomRegisterForm(UserCreationForm):
    username = forms.CharField(
        label="Логин",
        error_messages={'required': 'Обязательное поле.'},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите логин'})
    )
    password1 = forms.CharField(
        label="Пароль",
        error_messages={'required': 'Обязательное поле.'},
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'})
    )
    password2 = forms.CharField(
        label="Повторите пароль",
        error_messages={'required': 'Обязательное поле.'},
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Повторите пароль'})
    )

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')

# Форма пользователя для обновления (если надо менять email и т.д.)
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

# Форма профиля (аватар и т.п.)
class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']
