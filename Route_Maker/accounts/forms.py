from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Organization, User


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "nombre@negocio.com"}),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Tu contraseña"}),
    )


class RegistrationForm(UserCreationForm):
    organization_name = forms.CharField(
        label="Business name",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del emprendimiento"}),
    )
    first_name = forms.CharField(
        label="First name",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Tu nombre"}),
    )
    last_name = forms.CharField(
        label="Last name",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Tu apellido"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "nombre@negocio.com"}),
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Crea una contraseña"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Repite la contraseña"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("organization_name", "first_name", "last_name", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este email.")
        return email

    def save(self, commit=True):
        organization = Organization.objects.create(name=self.cleaned_data["organization_name"])
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.organization = organization
        user.role = User.Roles.OWNER
        if commit:
            user.save()
        return user
