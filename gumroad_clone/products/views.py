from django.conf import settings
from django.core.mail import send_mail
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .utils import checkout_session_create, stripe_webhook

from .forms import ProductModelForm
from .models import Product
from users.models import UserLibrary

User = get_user_model()


class ProductListView(generic.ListView):
    template_name = "discover.html"
    
    def get_queryset(self):       
        user_library = UserLibrary.objects.get(user=self.request.user)
        purchased_products = user_library.products.all()

        # Exclude own products
        queryset = Product.objects.exclude(user=self.request.user)
        # Exclude purchased products products
        queryset = queryset.difference(purchased_products)

        return queryset
    

class UserLibraryView(LoginRequiredMixin, generic.ListView):
    template_name = "library.html"
    
    def get_queryset(self):
        return UserLibrary.objects.get(user=self.request.user)

# User created products
class UserProductListView(LoginRequiredMixin, generic.ListView):
    template_name = "products.html"
        
    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)
    

class ProductCreateView(LoginRequiredMixin, generic.CreateView):
    template_name = "products/product_create.html"
    form_class = ProductModelForm

    def get_success_url(self):
        return reverse('user-products')

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.user = self.request.user
        instance.save()
        self.product = instance
        return super().form_valid(form)


class ProductUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "products/product_update.html"
    form_class = ProductModelForm

    def get_success_url(self):
        return reverse('user-products')

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)
    

class ProductDeleteView(LoginRequiredMixin, generic.DeleteView):
    template_name = "products/product_delete.html"

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse('user-products')


# Create a checkout session -> redirect(stripe)
checkout_session_create

# Stripe webhook for checkout session completed.
stripe_webhook


