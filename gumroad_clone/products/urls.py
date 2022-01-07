from django.urls import path
from products import views

app_name = "products"

urlpatterns = [
    path("<slug>/update/", views.ProductUpdateView.as_view(), name="product-update"),
    path("<slug>/delete/", views.ProductDeleteView.as_view(), name="product-delete"),
]
