from django.shortcuts import render
from .models import Product
import logging
log = logging.getLogger(__name__)


def all_products(request):
    log.info("Handling all_products %s request", request.method)
    products = Product.objects.all()
    return render(request, "products/products.html", {"products": products})


