from telegram.ext import CommandHandler, ConversationHandler
from telegram import ReplyKeyboardRemove
from state import is_booking_process_started, set_started_booking_process

async def cancel(update, context):
    if not is_booking_process_started(): 
        await update.message.reply_text("You haven't started the booking process. /create_booking to start.", reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("Booking process cancelled.", reply_markup=ReplyKeyboardRemove())
        set_started_booking_process(False)
    return ConversationHandler.END

cancel_handler = CommandHandler('cancel', cancel)
