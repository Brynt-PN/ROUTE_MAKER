from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Organization, User


COUNTRY_CHOICES = [
    ("pe", "Perú"),
    ("cl", "Chile"),
    ("co", "Colombia"),
    ("mx", "México"),
    ("ar", "Argentina"),
    ("bo", "Bolivia"),
    ("ec", "Ecuador"),
    ("us", "Estados Unidos"),
]


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


class OrganizationSettingsForm(forms.ModelForm):
    country_code = forms.ChoiceField(
        label="País base",
        choices=COUNTRY_CHOICES,
        widget=forms.Select(attrs={"class": "form-select route-input"}),
    )
    name = forms.CharField(
        label="Nombre del negocio",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control route-input", "placeholder": "Nombre del emprendimiento"}),
    )
    base_city = forms.CharField(
        label="Ciudad o zona base",
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control route-input", "placeholder": "Lima, Arequipa, Miraflores..."}),
    )
    base_location_name = forms.CharField(
        label="Origen operativo",
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control route-input route-autocomplete",
                "placeholder": "Dirección principal de despacho",
                "autocomplete": "off",
                "data-sync-lat-target": "id_base_lat",
                "data-sync-lon-target": "id_base_lon",
                "data-sync-country-target": "id_country_code",
            }
        ),
    )
    base_lat = forms.DecimalField(widget=forms.HiddenInput(), required=False)
    base_lon = forms.DecimalField(widget=forms.HiddenInput(), required=False)
    max_stops_per_route = forms.IntegerField(
        label="Máximo de paradas por ruta",
        min_value=1,
        max_value=30,
        widget=forms.NumberInput(attrs={"class": "form-control route-input", "placeholder": "8"}),
    )

    class Meta:
        model = Organization
        fields = ("name", "country_code", "base_city", "base_location_name", "base_lat", "base_lon", "max_stops_per_route")

    def clean_country_code(self):
        return self.cleaned_data["country_code"].lower()

    def clean(self):
        cleaned_data = super().clean()
        base_location_name = cleaned_data.get("base_location_name", "").strip()
        base_lat = cleaned_data.get("base_lat")
        base_lon = cleaned_data.get("base_lon")

        if not base_location_name:
            cleaned_data["base_lat"] = None
            cleaned_data["base_lon"] = None
            return cleaned_data

        if base_location_name and (base_lat is None or base_lon is None):
            self.add_error("base_location_name", "Selecciona el origen desde el autocompletado para guardar su ubicación.")

        return cleaned_data
