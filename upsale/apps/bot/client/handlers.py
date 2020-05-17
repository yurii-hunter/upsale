"""
Handlers for all commands for client part of a telegram bot
"""

from typing import List
from telegram import Update
from telegram.ext import CallbackContext
from upsale.apps.core.models import Buyer, Product, Cart, Pack, CartItem, Order
from .templates import welcome_message, select_product_message, product_view, \
    product_description_view, product_price_view, cart_is_empty_message, cart_message, \
    cart_item_view, total_price_view, cart_is_cleaned_message, get_contact_view, \
    get_city_view, get_branch_number_view, get_order_is_confirmed
from .helpers import respond, photo, edit, delete, data_id

def start_command(update: Update, context: CallbackContext) -> None:
    """Creates user in database and respond with welcome message"""
    user = update.effective_user
    (buyer, _) = Buyer.objects.get_or_create(
        id=user.id,
        defaults={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name':user.full_name,
            'name':user.name,
            'username':user.username,
            'language_code':user.language_code,
            'link':user.link,
            'is_bot':user.is_bot
            }
    )
    Cart.objects.get_or_create(
        user=buyer
    )
    respond(context.bot, update.effective_chat.id, welcome_message())

def products(update: Update, context: CallbackContext) -> None:
    """Respond with a list of available products"""
    respond(context.bot, update.effective_chat.id, select_product_message())
    for product in Product.objects.all():
        photo(context.bot, update.effective_chat.id, product_view(product))

def expand_product(update: Update, _: CallbackContext) -> None:
    """Respond with product description"""
    product = Product.objects.get(pk=data_id(update.callback_query.data))
    edit(update.callback_query, product_description_view(product))

def collapse_product(update: Update, _: CallbackContext) -> None:
    """Edit existing product message and hide description part"""
    product = Product.objects.get(pk=data_id(update.callback_query.data))
    edit(update.callback_query, product_view(product))

def prices(update: Update, _: CallbackContext) -> None:
    """Shows product packs / prices"""
    product = Product.objects.get(pk=data_id(update.callback_query.data))
    cart = Cart.objects.get(user=update.effective_user.id)
    edit(update.callback_query, product_price_view(product, cart))

def add_pack_to_cart(update: Update, _: CallbackContext) -> None:
    """Adds pack to cart"""
    cart = Cart.objects.get(user=update.effective_user.id)
    pack = Pack.objects.get(pk=data_id(update.callback_query.data))
    if not cart.contains(pack):
        cart.add_pack(pack)
    edit(update.callback_query, product_price_view(pack.product, cart))

def group_by_product(items: List[CartItem]):
    """Groups cart items by product"""
    products_group = dict()
    for item in items:
        if not item.pack.product in products_group:
            products_group[item.pack.product] = []
        products_group[item.pack.product].append(item)
    return products_group.values()

def show_cart(update: Update, context: CallbackContext) -> None:
    """Respond with all items in the cart"""
    cart = Cart.objects.get(user=update.effective_user.id)
    if cart.is_empty():
        respond(context.bot, update.effective_chat.id, cart_is_empty_message())
        return

    respond(context.bot, update.effective_chat.id, cart_message())
    groups = group_by_product(cart.cartitem_set.all())
    for group in groups:
        photo(context.bot, update.effective_chat.id, cart_item_view(group))

    price = cart.get_total_price()
    total_message = respond(context.bot, update.effective_chat.id, total_price_view(price))
    cart.total_message_id = total_message.message_id
    cart.save()

def increase_count(update: Update, context: CallbackContext):
    """Add one more pack to the cart"""
    cart = Cart.objects.get(user=update.effective_user.id)
    pack = Pack.objects.get(pk=data_id(update.callback_query.data))
    cart.increase_pack_count(pack)
    items = cart.cartitem_set.filter(pack__product=pack.product)
    edit(update.callback_query, cart_item_view(items))

    cart = Cart.objects.get(user=update.effective_user.id)
    price = cart.get_total_price()
    context.bot.edit_message_reply_markup(message_id=cart.total_message_id,
                                          chat_id=update.effective_chat.id,
                                          **total_price_view(price))

def decrease_count(update: Update, context: CallbackContext):
    """Remove pack from the cart"""
    cart = Cart.objects.get(user=update.effective_user.id)
    pack = Pack.objects.get(pk=data_id(update.callback_query.data))
    cart.decrease_pack_count(pack)
    items = cart.cartitem_set.filter(pack__product=pack.product)
    edit(update.callback_query, cart_item_view(items))

    cart = Cart.objects.get(user=update.effective_user.id)
    price = cart.get_total_price()
    context.bot.edit_message_reply_markup(message_id=cart.total_message_id,
                                          chat_id=update.effective_chat.id,
                                          **total_price_view(price))

def remove_pack(update: Update, context: CallbackContext):
    """Remove all packs of specific type from the cart"""
    cart = Cart.objects.get(user=update.effective_user.id)
    pack = Pack.objects.get(pk=data_id(update.callback_query.data))
    cart.remove_pack(pack)
    items = cart.cartitem_set.filter(pack__product=pack.product)
    if not items:
        delete(update, context)
    else:
        edit(update.callback_query, cart_item_view(items))

    price = cart.get_total_price()
    context.bot.edit_message_reply_markup(
        message_id=cart.total_message_id,
        chat_id=update.effective_chat.id,
        **total_price_view(price))

def clean_cart(update: Update, context: CallbackContext):
    """Remove all products from the cart"""
    cart = Cart.objects.get(user=update.effective_user.id)
    cart.cartitem_set.all().delete()
    respond(context.bot, update.effective_chat.id, cart_is_cleaned_message())
    respond(context.bot, update.effective_chat.id, welcome_message())

def confirm_order(update: Update, context: CallbackContext):
    """Confirm order"""
    user = Buyer.objects.get(pk=update.effective_user.id)
    cart = Cart.objects.get(user=update.effective_user.id)
    (order, order_just_created) = Order.objects.get_or_create(
        user=user
    )
    if order_just_created:
        for item in cart.cartitem_set.all():
            item.order = order
            item.cart = None
            item.save()
    if not user.phone_number:
        respond(context.bot, update.effective_chat.id, get_contact_view())
        return
    if not order.city:
        respond(context.bot, update.effective_chat.id, get_city_view())
        return
    if not order.branch_number:
        respond(context.bot, update.effective_chat.id, get_branch_number_view())
        return
    respond(context.bot, update.effective_chat.id, get_order_is_confirmed())

def save_contact(update: Update, _: CallbackContext):
    user = Buyer.objects.get(pk=update.effective_user.id)
    user.phone_number = update.message.contact.phone_number
    user.save()

def save_address(update: Update, context: CallbackContext):
    order = Order.objects.filter(user=update.effective_user.id, status='new')[0]
    if not order:
        return
    if not order.city:
        order.city = update.message.text
        order.save()
        confirm_order(update, context)
        return
    if not order.branch_number:
        order.branch_number = int(update.message.text)
        order.save()
        confirm_order(update, context)
        return
