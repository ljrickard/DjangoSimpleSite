from django.contrib import messages, auth
from accounts.forms import UserRegistrationForm, UserLoginForm
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.template.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.conf import settings
import stripe
import logging
import arrow
import json
from models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
log = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET


def register(request):
    log.info("Handling register %s request", request.method)
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():

            try:

                customer = stripe.Customer.create(
                    card=form.cleaned_data['stripe_id'],
                    description=form.cleaned_data['email'],
                    email=form.cleaned_data['email'],
                    plan='REG_MONTHLY'
                )

                log.info("customer %s", customer)

            except stripe.error.CardError:
                messages.error(request, "Your card was declined")

            if customer:
                user = form.save()
                user.stripe_id = customer.stripe_id
                user.subscription_end = arrow.now().replace(weeks=+4).datetime
                user.save()

                user = auth.authenticate(email=request.POST.get('email'), password=request.POST.get('password1'))

                if user:

                    messages.success(request, "You have successfully registered")
                    return redirect(reverse('profile'))

                else:
                    messages.error(request, "unable to log you in at this time!")
            else:
                messages.error(request, "We were unable to take payment with that card")

    else:
        form = UserRegistrationForm()

    args = {'form': form, 'publishable': settings.STRIPE_PUBLISHABLE}
    args.update(csrf(request))

    return render(request, 'register.html', args)


@login_required(login_url='/login/')
def profile(request):
    log.info("Handling profile %s request", request.method)
    return render(request, 'profile.html')


# Create your views here.
def login(request):
    log.info("Handling login %s request", request.method)
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = auth.authenticate(email=request.POST.get('email'), password=request.POST.get('password'))

            if user is not None:
                auth.login(request, user)
                messages.error(request, "You have successfully logged in")
                return redirect(reverse('profile'))
            else:
                form.add_error(None, "Your email or password was not recognised")

    else:
        form = UserLoginForm()

    args = {'form': form}
    args.update(csrf(request))
    return render(request, 'login.html', args)


def logout(request):
    log.info("Handling logout %s request", request.method)
    auth.logout(request)
    messages.success(request, 'You have successfully logged out')
    return redirect(reverse('index'))


@login_required(login_url='/login/')
def topup(request):
    log.info("Handling topup %s request", request.method)

    charge = stripe.Charge.create(
        amount=99,
        currency="USD",
        customer=request.user.stripe_id
    )

    log.info("charge %s", charge)

    return redirect(reverse('profile'))


@login_required(login_url='/login/')
def cancel_subscription(request):
    log.info("Handling cancel_subscription %s request", request.method)
    try:
        customer = stripe.Customer.retrieve(request.user.stripe_id)
        customer.cancel_subscription(at_period_end=False)
        log.info("customer=%s", customer)
    except Exception, e:
        messages.error(request, e)
    return redirect('profile')


@csrf_exempt
def subscriptions_webhook(request):
    log.info("Handling subscriptions_webhook %s request", request.method)
    event_json = json.loads(request.body)
    try:
        #only for live
        #event = = stripe.Event.retrieve(event_json['object']['id'])
        cust = event_json['object']['customer']
        paid = event_json['object']['paid']
        user = User.objects.get(stripe_id=cust)
        if user and paid:
            user.subscription_end = arrow.now().replace(weeks=+4).datetime
            user.save()
    except stripe.InvalidRequestError:
        log.info("Returning HttpResponse(status=404) %s request", request.method)
        return HttpResponse(status=404)
    log.info("Returning HttpResponse(status=200) %s request", request.method)
    return HttpResponse(status=200)





