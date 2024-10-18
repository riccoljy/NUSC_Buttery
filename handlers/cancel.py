from telegram.ext import CommandHandler, ConversationHandler
from telegram import ReplyKeyboardRemove

async def cancel(update, context):
    await update.message.reply_text("Booking process cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

cancel_handler = CommandHandler('cancel', cancel)
