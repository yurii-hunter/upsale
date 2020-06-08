"""
An entry point for client part of the bot.
Here are registered handlers for all commands.
"""

from django.core.management.base import BaseCommand
from telegram.ext import Updater
from telegram.ext import CommandHandler, Filters, MessageHandler, CallbackQueryHandler
from upsale.settings import BOTS
from upsale.apps.bot.client.handlers import start_command, products, expand_product, \
    collapse_product, prices, add_sku_to_cart, show_cart, increase_count, decrease_count, \
    remove_sku, clean_cart, confirm_order, save_contact, save_address
from upsale.apps.bot.client.constant import GO_BUTTON, CART_BUTTON, EXIT_BUTTON, \
    PRODUCTS_BUTTON, CONFIRM_BUTTON


class Command(BaseCommand):
    """Creates bot dispatcher and register all commands"""
    help = 'Starts the client telegram bot'

    def handle(self, *args, **options):
        updater = Updater(token=BOTS['client']['API_TOKEN'], use_context=True)
        dispatcher = updater.dispatcher

        dispatcher.add_handler(CommandHandler('start', start_command))

        dispatcher.add_handler(MessageHandler(Filters.text(GO_BUTTON), products))
        dispatcher.add_handler(MessageHandler(Filters.text(PRODUCTS_BUTTON), products))
        dispatcher.add_handler(MessageHandler(Filters.text(EXIT_BUTTON), start_command))
        dispatcher.add_handler(MessageHandler(Filters.text(CART_BUTTON), show_cart))
        dispatcher.add_handler(MessageHandler(Filters.text(CONFIRM_BUTTON), confirm_order))
        dispatcher.add_handler(MessageHandler(Filters.contact, save_contact))
        dispatcher.add_handler(MessageHandler(Filters.all, save_address))

        dispatcher.add_handler(CallbackQueryHandler(expand_product, pattern='.*description.*'))
        dispatcher.add_handler(CallbackQueryHandler(collapse_product, pattern='.*product.*'))
        dispatcher.add_handler(CallbackQueryHandler(prices, pattern='.*show_prices.*'))
        dispatcher.add_handler(CallbackQueryHandler(add_sku_to_cart, pattern='.*add_to_cart.*'))
        dispatcher.add_handler(CallbackQueryHandler(increase_count, pattern='.*plus_one.*'))
        dispatcher.add_handler(CallbackQueryHandler(decrease_count, pattern='.*minus_one.*'))
        dispatcher.add_handler(CallbackQueryHandler(remove_sku, pattern='.*remove_one.*'))
        dispatcher.add_handler(CallbackQueryHandler(clean_cart, pattern='clean_cart'))

        updater.start_polling()
        updater.idle()
        