from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import logging
log = logging.getLogger(__name__)


@csrf_exempt
def paypal_return(request):
    log.info("Handling paypal_return %s request", request.method)
    args = {'post': request.POST, 'get': request.GET}
    return render(request, 'paypal/paypal_return.html', args)


def paypal_cancel(request):
    log.info("Handling paypal_cancel %s request", request.method)
    args = {'post': request.POST, 'get': request.GET}
    return render(request, 'paypal/paypal_cancel.html', args)

