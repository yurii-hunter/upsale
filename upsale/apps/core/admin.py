from django.contrib import admin
from .models import Buyer, Product, Pack, Cart, CartItem, Order

admin.site.register(Buyer)
admin.site.register(Product)
admin.site.register(Pack)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
