from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


class Organization(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    country_code = models.CharField(max_length=2, default="pe")
    base_city = models.CharField(max_length=120, blank=True)
    base_location_name = models.CharField(max_length=200, blank=True)
    base_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    base_lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    max_stops_per_route = models.PositiveSmallIntegerField(default=8)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "organization"
            candidate = base_slug
            suffix = 1
            while Organization.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                suffix += 1
                candidate = f"{base_slug}-{suffix}"
            self.slug = candidate
        super().save(*args, **kwargs)


class User(AbstractUser):
    class Roles(models.TextChoices):
        OWNER = "owner", "Owner"
        OPERATOR = "operator", "Operator"

    username = None
    email = models.EmailField(unique=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
    )
    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.OWNER,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return self.email
