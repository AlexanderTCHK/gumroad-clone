from django.conf import settings
from django.core.mail import send_mail
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_protect

import stripe

from .forms import ProductModelForm
from .models import Product, PurchasedProduct

User = get_user_model()

stripe.api_key = settings.STRIPE_SECRET_KEY

class ProductListView(generic.ListView):
    template_name = "discover.html"
    queryset = Product.objects.filter(active=True)


class ProductDetailView(generic.DetailView):
    template_name = "products/product.html"
    queryset = Product.objects.all()
    
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        if self.request.user.is_authenticated:
            if product in self.request.user.userlibrary.products.all():
                context.update({
                    "has_access": True
                })
        return context
    


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


@csrf_exempt
def checkout_session_create(request, *args, **kwargs):
    product = Product.objects.get(slug=kwargs['slug'])
    domain = "https://domain.com"
    if settings.DEBUG:
        domain = "http://127.0.0.1:80"

    customer = None
    customer_email = None
    if request.user.is_authenticated:
        if request.user.stripe_customer_id:
            customer = request.user.stripe_customer_id
        else:
            customer_email = request.user.email
    
    # dummy for local dev
    product_image_urls = ["https://dummyimage.com/420x260"]
    if product.cover:
        if not settings.DEBUG:
            product_image_urls.append(product.cover.url)


    session = stripe.checkout.Session.create(
    customer=customer,
    customer_email=customer_email,
    line_items=[{
        'price_data': {
          'currency': 'usd',
          'product_data': {
            'name': product.name,
            'images': product_image_urls
          },
          'unit_amount': product.price,
        },
        'quantity': 1,
    }],
    payment_intent_data={
        'application_fee_amount': 100,
        'transfer_data': {
        'destination': product.user.stripe_account_id,
        },
    },
    mode='payment',
    success_url=domain + reverse("success"),
    cancel_url=domain + reverse("discover"),
    metadata={
        "product_id": product.id
    }
    )
    return redirect(session.url)



class SuccessView(generic.TemplateView):
    template_name = "success.html"

@csrf_exempt
def stripe_webhook(request, *args, **kwargs):
    CHECKOUT_SESSION_COMPLETED = "checkout.session.completed"
    ACCOUNT_UPDATED = "account.updated"

    endpoint_secret = settings.STRIPE__WEBHOOK_SECRET
    event = None
    payload = request.body
    print(payload)
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e
    # Handle the event
    print('Unhandled event type {}'.format(event['type']))
    if event['type'] == CHECKOUT_SESSION_COMPLETED:
            print(event)

            product_id = event["data"]["object"]["metadata"]["product_id"]
            product = Product.objects.get(id=product_id)
            
            stripe_customer_id = event["data"]["object"]["customer"]
            try:
                user = User.objects.get(stripe_customer_id=stripe_customer_id)
                user.userlibrary.products.add(product)
                
                # give access to this product
            except User.DoesNotExist:
                # assign the customer_id to the corresponding user
                stripe_customer_email = event["data"]["object"]["customer_details"]["email"]

                try:
                    user = User.objects.get(email=stripe_customer_email)
                    print("The user doesn't have a stripe customer id", user.email)
                    user.stripe_customer_id = stripe_customer_id
                    user.save()
                    user.userlibrary.products.add(product)

                except User.DoesNotExist:
                    PurchasedProduct.objects.create(email=stripe_customer_email, product=product)
                    send_mail(
                        subject="Create an account to access your content",
                        message="Please signup to access your latest purchase",
                        recipient_list=[stripe_customer_email],
                        from_email="test@admingumroad.com"
                    )
                    print("User.DoesNotExist")             
    

    else:
        # event["type"] == ACCOUNT_UPDATED:
        print(event)


    return HttpResponse()