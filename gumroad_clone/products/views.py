from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.http import JsonResponse

import json

from .forms import ProductModelForm
from .models import Product

class ProductListView(generic.ListView):
    template_name = "discover.html"
    queryset = Product.objects.filter(active=True)


class ProductDetailView(generic.DetailView):
    template_name = "products/product.html"
    queryset = Product.objects.all()
    context_object_name = "product"


class UserProductListView(LoginRequiredMixin, generic.ListView):
    # perconal products
    template_name = "products.html"
    
    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)
    

class ProductCreateView(LoginRequiredMixin, generic.CreateView):
    template_name = "products/product_create.html"
    form_class = ProductModelForm

    def get_success_url(self):
        return reverse('products:product-detail', kwargs={
            "slug": self.product.slug
        })

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
        return reverse('products:product-detail', kwargs={
            "slug": self.get_object().slug
        })

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)
    

class ProductDeleteView(LoginRequiredMixin, generic.DeleteView):
    template_name = "products/product_delete.html"

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse('user-products')

def paymentComplete(request):
    body = json.loads(request.body)
    print("Body:", body)
    product = Product.objects.get(name=body['product'])
    
    return JsonResponse("Payment complete", safe=False)
