from django.db import models
from django.urls import reverse
import random

class Product(models.Model):

    def random_star():
        return "{0:.1f}".format(random.uniform(4, 5))

    def random_review():
        return "{}".format(random.randint(1, 1670))

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="products"
    )
    name = models.CharField(max_length=100)
    description = models.TextField()
    cover = models.ImageField(null=True, blank=True, upload_to="product_covers")
    slug = models.SlugField(unique=True)

    # content
    content_url = models.URLField(null=True, blank=True)
    content_file = models.FileField(null=True, blank=True)

    published = models.BooleanField(default=False)
    price = models.PositiveIntegerField(default=1) # in cents

    # etc.
    star = models.FloatField(default=random_star)
    num_reviews = models.PositiveIntegerField(default=random_review)

    def __str__(self):
        return self.name

    def get_update_url(self):
        return reverse("products:product-update", kwargs={"slug": self.slug})

    def get_delete_url(self):
        return reverse("products:product-delete", kwargs={"slug": self.slug})
    
    def price_display(self):
        return "{0:.2f}".format(self.price/100)

class PurchasedProduct(models.Model):
    email = models.EmailField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date_purchased = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
    