import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, RedirectView, UpdateView, TemplateView
from stripe.api_resources import account_link

User = get_user_model()

stripe.api_key = settings.STRIPE_SECRET_KEY

class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        account = stripe.Account.retrieve(self.request.user.stripe_account_id)
        details_submitted = account["details_submitted"]
        contex = super().get_context_data(**kwargs)
        contex.update({
            'details_submitted': details_submitted
        })
        return contex
    

class UserDetailView(LoginRequiredMixin, DetailView):

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):

    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self):
        assert (
            self.request.user.is_authenticated
        )  # for mypy to know that the user is authenticated
        return self.request.user.get_absolute_url()

    def get_object(self):
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):

    permanent = False

    def get_redirect_url(self):
        return reverse("discover")

user_redirect_view = UserRedirectView.as_view()

class StripeAccountLink(LoginRequiredMixin, RedirectView):

    permanent = False

    def get_redirect_url(self):
        # Domain for success and cancel urls
        domain = "http://" + settings.ALLOWED_HOSTS[0]

        account_link = stripe.AccountLink.create(
            account = self.request.user.stripe_account_id,
            refresh_url = domain + reverse("stripe-account-link"),
            return_url = domain + reverse("profile"),
            type = "account_onboarding",
        )
        return account_link["url"]