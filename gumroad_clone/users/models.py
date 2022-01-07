import stripe
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.db import  models
from django.db.models.signals import post_save
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from products.models import Product, PurchasedProduct

stripe.api_key = settings.STRIPE_SECRET_KEY

class User(AbstractUser):
    """Default user for Gumroad Clone."""

    #: First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    
    # Stripe account for purchasing
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    # Stripe account for selling
    stripe_account_id = models.CharField(max_length=100)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})


class UserLibrary(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, blank=True)

    class Meta:
        verbose_name_plural = "UserLibraries"

    def __str__(self):
        return self.user.username

def create_userlibrary_post_user(sender, instance, created, **kwargs):
    if created:
        library = UserLibrary.objects.create(user=instance)

        # assign all the anonymous  checkouts / products they purchased
        purchased_products = PurchasedProduct.objects.filter(email=instance.email)
        for purchased_product in purchased_products:
            library.products.add(purchased_product.product)
        
        # Create a stripe_account_id for all Users
        account = stripe.Account.create(type = "express")
        instance.stripe_account_id = account["id"]
        instance.save()

post_save.connect(create_userlibrary_post_user, sender=User)