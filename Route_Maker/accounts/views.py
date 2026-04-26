from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import LoginForm, OrganizationSettingsForm, RegistrationForm


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("landing")


class UserLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class UserRegisterView(FormView):
    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("landing")


@login_required
def organization_settings(request):
    organization = request.user.organization
    if organization is None:
        messages.error(request, "Tu usuario no tiene un negocio asociado todavía.")
        return redirect("dashboard")

    if request.method == "POST":
        form = OrganizationSettingsForm(request.POST, instance=organization)
        if form.is_valid():
            form.save()
            messages.success(request, "La configuración del negocio fue actualizada.")
            return redirect("accounts:settings")
    else:
        form = OrganizationSettingsForm(instance=organization)

    return render(
        request,
        "accounts/settings.html",
        {
            "form": form,
            "organization_name": organization.name,
        },
    )
