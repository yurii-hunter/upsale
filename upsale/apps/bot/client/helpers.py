from ast import literal_eval
from upsale.apps.bot.client.constant import ID

def respond(bot, chat_id, message):
    return bot.send_message(chat_id=chat_id, **message)

def photo(bot, chat_id, message):
    bot.send_photo(chat_id=chat_id, **message)

def edit(query, message):
    query.edit_message_caption(**message)

def delete(update, context):
    context.bot.delete_message(update.effective_chat.id, update.effective_message.message_id)

def data_id(data):
    literal = literal_eval(data)
    return literal[ID]
    