from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.shortcuts import redirect
from django.core.mail import send_mail
from django.http import HttpResponse
from .models import Product, PurchasedProduct
from users.models import User

import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

# Create a checkout session -> redirect(stripe)
@csrf_exempt
def checkout_session_create(request, *args, **kwargs):
    product = Product.objects.get(slug=kwargs['slug'])
    
    # Domain for success and cancel urls
    domain = "http://" + settings.ALLOWED_HOSTS[0]

    # Get or create customer logic
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

    # Create a session
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
    success_url=domain + reverse("user-library"),
    cancel_url=domain + reverse("discover"), 
    metadata={
        "product_id": product.id
    }
    )
    return redirect(session.url)

# Stripe webhook for checkout session completed.
@csrf_exempt
def stripe_webhook(request, *args, **kwargs):
    CHECKOUT_SESSION_COMPLETED = "checkout.session.completed"
    ACCOUNT_UPDATED = "account.updated"

    endpoint_secret = settings.STRIPE__WEBHOOK_SECRET
    event = None
    payload = request.body
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
    print(event)
    if event['type'] == CHECKOUT_SESSION_COMPLETED:
            product_id = event["data"]["object"]["metadata"]["product_id"]
            product = Product.objects.get(id=product_id)
            stripe_customer_id = event["data"]["object"]["customer"]
            # User authenticated and has a stripe_customer_id
            try:
                
                user = User.objects.get(stripe_customer_id=stripe_customer_id)
                user.userlibrary.products.add(product)
            # User authenticated and has NO stripe_customer_id           
            except User.DoesNotExist:
                stripe_customer_email = event["data"]["object"]["customer_details"]["email"]
                # Assign a stripe_customer_id to authenticated User
                try:
                    user = User.objects.get(email=stripe_customer_email)
                    user.stripe_customer_id = stripe_customer_id
                    user.save()
                    user.userlibrary.products.add(product)
                # User isn't authenticated and has NO stripe_customer_id   
                except User.DoesNotExist:
                    PurchasedProduct.objects.create(email=stripe_customer_email, product=product)
                    send_mail(
                        subject="Create an account to access your content",
                        message="Please signup to access your latest purchase",
                        recipient_list=[stripe_customer_email],
                        from_email="test@admingumroad.com"
                    )           
    

    else:
        # event["type"] == ACCOUNT_UPDATED:
        # TODO: add more functionality
        pass


    return HttpResponse()    