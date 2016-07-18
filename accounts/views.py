from django.contrib import messages, auth
from accounts.forms import UserRegistrationForm, UserLoginForm
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.template.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.conf import settings
import stripe
import logging
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
                )

                log.info("customer %s", customer)

                charge = stripe.Charge.create(
                    amount=100,
                    currency="USD",
                    customer=customer.stripe_id
                )

                log.info("charge %s", charge)

            except stripe.error.CardError:
                messages.error(request, "Your card was declined")

            if charge.paid:
                form.save()

                user = auth.authenticate(email=request.POST.get('email'), password=request.POST.get('password1'))

                if user:
                    user.stripe_id = customer.stripe_id
                    user.save()
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

