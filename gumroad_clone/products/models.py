from django.db import models
from django.urls import reverse

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    cover = models.ImageField(null=True, blank=True, upload_to="product_covers")
    slug = models.SlugField()

    # content
    content_url = models.URLField(null=True, blank=True)
    content_file = models.FileField(null=True, blank=True)

    price = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:product-detail", kwargs={"slug": self.slug})
    

    def price_display(self):
        return "{0:.2f}".format(self.price/100)