"""
Build messages
"""

from typing import List
import itertools
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from upsale.apps.core.models import Product, Cart, StockKeepingUnit
from upsale.apps.bot.client.constant import ID, ACTION
from upsale.apps.bot.client.constant import GO_BUTTON, CART_BUTTON, EXIT_BUTTON, \
    PRODUCTS_BUTTON, CONFIRM_BUTTON, EMPTY_CART_BUTTON


def get_show_description_button(product_id: int) -> InlineKeyboardButton:
    callback = str({ID: product_id, ACTION: 'description'})
    return InlineKeyboardButton("Описание товара", callback_data=callback)


def get_add_to_cart_button(product_id: int) -> InlineKeyboardButton:
    callback = str({ID: product_id, ACTION: 'show_prices'})
    return InlineKeyboardButton("Добавить в корзину", callback_data=callback)


def get_hide_description_button(product_id: str) -> InlineKeyboardButton:
    callback = str({ID: product_id, ACTION: 'product'})
    return InlineKeyboardButton('Скрыть описание', callback_data=callback)


def get_back_button(product_id: str) -> InlineKeyboardButton:
    callback = str({ID: product_id, ACTION: 'product'})
    return InlineKeyboardButton("Назад", callback_data=callback)


def get_plus_button(pack_id: str) -> InlineKeyboardButton:
    callback = str({ID: pack_id, ACTION: 'plus_one'})
    return InlineKeyboardButton("➕", callback_data=callback)


def get_minus_button(pack_id: str) -> InlineKeyboardButton:
    callback = str({ID: pack_id, ACTION: 'minus_one'})
    return InlineKeyboardButton("➖", callback_data=callback)


def get_remove_button(pack_id: str) -> InlineKeyboardButton:
    callback = str({ID: pack_id, ACTION: 'remove_one'})
    return InlineKeyboardButton("❌", callback_data=callback)


def welcome_message() -> dict:
    go_button = [[GO_BUTTON]]
    action_markup = ReplyKeyboardMarkup(
        go_button, one_time_keyboard=False, resize_keyboard=True)
    return {
        'text': f"Чтобы сделать новый заказ нажмите '{GO_BUTTON}'",
        'reply_markup': action_markup
    }


def select_product_message() -> dict:
    action_buttons = [[CART_BUTTON], [EXIT_BUTTON]]
    reply_markup = ReplyKeyboardMarkup(
        action_buttons, one_time_keyboard=False, resize_keyboard=True)
    return {
        'text': 'Давай выберем что-то вкусненькое!',
        'reply_markup': reply_markup
    }


def cart_is_empty_message():
    return {'text': "В корзине пока пусто"}


def cart_message() -> dict:
    action_buttons = [[PRODUCTS_BUTTON, CONFIRM_BUTTON], [EXIT_BUTTON]]
    reply_markup = ReplyKeyboardMarkup(action_buttons, one_time_keyboard=False, resize_keyboard=True)
    return {'text': CART_BUTTON, 'reply_markup': reply_markup}


def product_view(product: Product) -> dict:
    action_buttons = [[get_show_description_button(product.id)],
                      [get_add_to_cart_button(product.id)]]
    action_markup = InlineKeyboardMarkup(action_buttons)
    return {'caption': product.short_caption(), 'photo': product.image, 'reply_markup': action_markup}


def product_description_view(product: Product) -> dict:
    action_buttons = [[get_hide_description_button(product.id)],
                      [get_add_to_cart_button(product.id)]]
    action_markup = InlineKeyboardMarkup(action_buttons)
    return {'caption': product.long_caption(), 'photo': product.image, 'reply_markup': action_markup}


def product_price_view(product: Product, cart: Cart) -> dict:
    action_buttons = [get_back_button(product.id)]
    for sku in product.stockkeepingunit_set.all():
        if cart.contains(sku):
            price_button = InlineKeyboardButton(
                text=f'{sku.pack.size}{sku.pack.unit} - {sku.price} грн - В корзине', callback_data='empty')
        else:
            callback = str({ID: sku.id, ACTION: 'add_to_cart'})
            price_button = InlineKeyboardButton(text=f'{sku.pack.size}{sku.pack.unit} - {sku.price} грн', callback_data=callback)
        action_buttons.append(price_button)
    action_markup = InlineKeyboardMarkup.from_column(action_buttons)
    return {'caption': product.short_caption(), 'reply_markup': action_markup}


def cart_item_view(product, sku_set):
    buttons = []
    items = sorted(sku_set, key=lambda x: x.id)
    groups = itertools.groupby(items, lambda x: x)
    for sku, group in groups:
        plus = get_plus_button(sku.id)
        minus = get_minus_button(sku.id)
        remove = get_remove_button(sku.id)
        count = InlineKeyboardButton(f'{len(list(group))}/{sku.pack.size}{sku.pack.unit}', callback_data='empty')
        buttons.append([plus, count, minus, remove])
    reply_markup = InlineKeyboardMarkup(buttons, one_time_keyboard=False, resize_keyboard=True)
    return {'caption': product.short_caption(), 'photo': product.image, 'reply_markup': reply_markup}


def total_price_view(price):
    buttons = [InlineKeyboardButton(f'{price} грн', callback_data='empty'),
               InlineKeyboardButton(EMPTY_CART_BUTTON, callback_data='clean_cart')]
    reply_markup = InlineKeyboardMarkup.from_column(buttons)
    return {'text': 'Общая сумма заказа:', 'reply_markup': reply_markup}


def cart_is_cleaned_message():
    return {'text': "Корзина очищена"}
  

def get_contact_view():
    button = KeyboardButton("Отправить номер", request_contact=True, one_time_keyboard=True)
    reply_markup = ReplyKeyboardMarkup.from_button(button, resize_keyboard=True)
    return {
        'reply_markup': reply_markup,
        'text': 'Ваш номер телефона нужен, чтобы мы могли отправить посылку новой почтой'}

def get_city_view():
    """Get delivery city"""
    return {'text': "Укажите город доставки"}

def get_branch_number_view():
    """Get delivery branch number"""
    return {'text': "Укажите номер отделения Новой Почты"}

def get_order_is_confirmed():
    """Confirm order"""
    return {'text': "Заказ успешно оформлен. Мы свяжемся с вами если нужно будет уточнить детали"}
