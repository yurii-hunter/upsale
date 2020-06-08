"""
Handlers for all commands for client part of a telegram bot
"""

from typing import List
import itertools
from telegram import Update
from telegram.ext import CallbackContext
from upsale.apps.core import models
from . import templates as views
from . import helpers

def start_command(update: Update, context: CallbackContext) -> None:
    """Creates user in database and respond with welcome message"""
    user = update.effective_user
    (buyer, _) = models.Buyer.objects.get_or_create(
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
    models.Cart.objects.get_or_create(
        buyer=buyer
    )
    helpers.respond(context.bot, update.effective_chat.id, views.welcome_message())

def products(update: Update, context: CallbackContext) -> None:
    """Respond with a list of available products"""
    helpers.respond(context.bot, update.effective_chat.id, views.select_product_message())
    for product in models.Product.objects.all():
        helpers.photo(context.bot, update.effective_chat.id, views.product_view(product))

def expand_product(update: Update, _: CallbackContext) -> None:
    """Respond with product description"""
    product = models.Product.objects.get(pk=helpers.data_id(update.callback_query.data))
    helpers.edit(update.callback_query, views.product_description_view(product))

def collapse_product(update: Update, _: CallbackContext) -> None:
    """Edit existing product message and hide description part"""
    product = models.Product.objects.get(pk=helpers.data_id(update.callback_query.data))
    helpers.edit(update.callback_query, views.product_view(product))

def prices(update: Update, _: CallbackContext) -> None:
    """Shows product packs / prices"""
    product = models.Product.objects.get(pk=helpers.data_id(update.callback_query.data))
    cart = models.Cart.objects.get(buyer=update.effective_user.id)
    helpers.edit(update.callback_query, views.product_price_view(product, cart))

def add_sku_to_cart(update: Update, _: CallbackContext) -> None:
    """Adds sku to cart"""
    cart = models.Cart.objects.get(buyer=update.effective_user.id)
    sku = models.StockKeepingUnit.objects.get(pk=helpers.data_id(update.callback_query.data))
    if not cart.contains(sku):
        cart.add_sku(sku)
    helpers.edit(update.callback_query, views.product_price_view(sku.product, cart))

def show_cart(update: Update, context: CallbackContext) -> None:
    """Respond with all items in the cart"""
    cart = models.Cart.objects.get(buyer=update.effective_user.id)
    if cart.is_empty():
        helpers.respond(context.bot, update.effective_chat.id, views.cart_is_empty_message())
        return

    helpers.respond(context.bot, update.effective_chat.id, views.cart_message())
    items = sorted(cart.items.all(), key=lambda x: x.product.id)
    groups = itertools.groupby(items, lambda x: x.product)
    for product, group in groups:
        helpers.photo(context.bot, update.effective_chat.id, views.cart_item_view(product, group))

    price = cart.get_total_price()
    total_message = helpers.respond(context.bot, update.effective_chat.id, views.total_price_view(price))
    cart.total_message_id = total_message.message_id
    cart.save()

def increase_count(update: Update, context: CallbackContext):
    """Add one more pack to the cart"""
    cart = models.Cart.objects.get(buyer=update.effective_user.id)
    sku = models.StockKeepingUnit.objects.get(pk=helpers.data_id(update.callback_query.data))
    cart.add_sku(sku)
    items = cart.items.filter(product=sku.product)
    helpers.edit(update.callback_query, views.cart_item_view(sku.product, items))

    price = cart.get_total_price()
    context.bot.edit_message_reply_markup(message_id=cart.total_message_id,
                                          chat_id=update.effective_chat.id,
                                          **views.total_price_view(price))

def decrease_count(update: Update, context: CallbackContext):
    """Remove sku from the cart"""
    cart = models.Cart.objects.get(buyer=update.effective_user.id)
    sku = models.StockKeepingUnit.objects.get(pk=helpers.data_id(update.callback_query.data))
    cart.remove_sku(sku)
    items = cart.items.filter(product=sku.product)
    helpers.edit(update.callback_query, views.cart_item_view(sku.product, items))

    price = cart.get_total_price()
    context.bot.edit_message_reply_markup(message_id=cart.total_message_id,
                                          chat_id=update.effective_chat.id,
                                          **views.total_price_view(price))

def remove_sku(update: Update, context: CallbackContext):
    """Remove all packs of specific type from the cart"""
    cart = models.Cart.objects.get(buyer=update.effective_user.id)
    sku = models.StockKeepingUnit.objects.get(pk=helpers.data_id(update.callback_query.data))
    cart.clear_sku(sku)
    items = cart.items.filter(product=sku.product)
    helpers.edit(update.callback_query, views.cart_item_view(sku.product, items))

    price = cart.get_total_price()
    context.bot.edit_message_reply_markup(
        message_id=cart.total_message_id,
        chat_id=update.effective_chat.id,
        **views.total_price_view(price))

def clean_cart(update: Update, context: CallbackContext):
    """Remove all products from the cart"""
    cart = models.Cart.objects.get(buyer=update.effective_user.id)
    cart.items.clear()
    helpers.respond(context.bot, update.effective_chat.id, views.cart_is_cleaned_message())
    helpers.respond(context.bot, update.effective_chat.id, views.welcome_message())

def confirm_order(update: Update, context: CallbackContext):
    """Confirm order"""
    user = models.Buyer.objects.get(pk=update.effective_user.id)
    cart = models.Cart.objects.get(user=update.effective_user.id)
    (order, order_just_created) = models.Order.objects.get_or_create(
        user=user
    )
    if order_just_created:
        for item in cart.cartitem_set.all():
            item.order = order
            item.cart = None
            item.save()
    if not user.phone_number:
        helpers.respond(context.bot, update.effective_chat.id, views.get_contact_view())
        return
    if not order.city:
        helpers.respond(context.bot, update.effective_chat.id, views.get_city_view())
        return
    if not order.branch_number:
        helpers.respond(context.bot, update.effective_chat.id, views.get_branch_number_view())
        return
    helpers.respond(context.bot, update.effective_chat.id, views.get_order_is_confirmed())

def save_contact(update: Update, _: CallbackContext):
    user = models.Buyer.objects.get(pk=update.effective_user.id)
    user.phone_number = update.message.contact.phone_number
    user.save()

def save_address(update: Update, context: CallbackContext):
    order = models.Order.objects.filter(user=update.effective_user.id, status='new')[0]
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
