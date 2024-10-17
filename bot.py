from flask import Flask, request
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Get the API token and other necessary configurations from environment variables
API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')
MESSAGE_THREAD_ID = os.getenv('MESSAGE_THREAD_ID')

# Create an instance of the Application
application = Application.builder().token(API_TOKEN).build()

# Define conversation states
ASK_BUTTERY, ASK_DATE, ASK_DURATION, ASK_PURPOSE, ASK_TIME = range(5)

# Reply keyboard markup configurations
reply_markup_buttery = ReplyKeyboardMarkup([["Saga Buttery", "Elm Buttery"]], one_time_keyboard=True, resize_keyboard=True)
reply_markup_duration = ReplyKeyboardMarkup([['1', '2', '3', '4']], one_time_keyboard=True, resize_keyboard=True)

SGT = timezone(timedelta(hours=8))

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Let's start your booking for the Buttery!\n"
        "If you don't wish to continue, click /cancel\n"
    )
    return ASK_BUTTERY

async def create_booking(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Hey! Which buttery would you like to book?",
        reply_markup=reply_markup_buttery
    )
    return ASK_BUTTERY

async def ask_buttery(update: Update, context: CallbackContext) -> int:
    chosen_buttery = update.message.text

    # Validate the chosen buttery
    if chosen_buttery not in ["Saga Buttery", "Elm Buttery"]:
        await update.message.reply_text(
            "Please select a valid buttery.",
            reply_markup=reply_markup_buttery
        )
        return ASK_BUTTERY
    
    context.user_data['chosen_buttery'] = chosen_buttery
    await ask_for_date(update, context)
    return ASK_DATE

async def ask_for_date(update: Update, context: CallbackContext) -> None:
    today = datetime.now(SGT).strftime("%d/%m/%Y")
    max_date = (datetime.now(SGT) + timedelta(days=30)).strftime("%d/%m/%Y")

    await update.message.reply_text(
        f"What date would you like to book the {context.user_data['chosen_buttery']}? \n"
        f"Send date in DD/MM/YYYY format, or /today or /tomorrow.\n\n"
        f"Date must be between {today} and {max_date}.",
        reply_markup=ReplyKeyboardRemove()
    )

async def ask_date(update: Update, context: CallbackContext) -> int:
    date_str = update.message.text

    # Handle /today and /tomorrow commands
    if date_str in ["/today", "/tomorrow"]:
        selected_date = datetime.now(SGT).replace(hour=0, minute=0, second=0, microsecond=0)
        if date_str == "/tomorrow":
            selected_date += timedelta(days=1)
        
        context.user_data['booking_date'] = selected_date.strftime("%d/%m/%Y")
        await update.message.reply_text(f"Your booking has been selected for {date_str[1:]} ({context.user_data['booking_date']}).")
        await update.message.reply_text("What time is your booking?")
        return ASK_TIME

    # Validate normal date input
    try:
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        today = datetime.now(SGT).replace(hour=0, minute=0, second=0, microsecond=0)
        max_date = today + timedelta(days=30)
        
        if today <= date_obj <= max_date:
            context.user_data['booking_date'] = date_str
            await update.message.reply_text("What time is your booking?")
            return ASK_TIME
        else:
            await update.message.reply_text("Please enter a valid date between today and one month from now.")
            return ASK_DATE
    except ValueError:
        await update.message.reply_text("Invalid date format. Please send the date in DD/MM/YYYY format.")
        return ASK_DATE
    
async def ask_time(update:Update, context: CallbackContext) -> int:
    context.user_data['booking_time'] = update.message.text
    await update.message.reply_text("How long is your booking? (Please send a time range of 1 to 4 hours)", reply_markup=reply_markup_duration)
    return ASK_DURATION

async def ask_duration(update: Update, context: CallbackContext) -> int:
    try:
        duration = int(update.message.text)
        if 1 <= duration <= 4:
            context.user_data['duration'] = duration
            await update.message.reply_text("What is the purpose of this booking?", reply_markup=ReplyKeyboardRemove())
            return ASK_PURPOSE
        else:
            await update.message.reply_text("Please select a duration between 1 and 4 hours.", reply_markup=reply_markup_duration)
            return ASK_DURATION
    except ValueError:
        await update.message.reply_text("Please select a valid number for the duration of booking.")
        return ASK_DURATION

async def ask_purpose(update: Update, context: CallbackContext) -> int:
    purpose = update.message.text
    context.user_data['purpose'] = purpose
    telehandle = update.message.from_user.username

    booking_details = (
        f"Booking Request by @{telehandle}:\n"
        f"Buttery: {context.user_data['chosen_buttery']}\n"
        f"Date: {context.user_data['booking_date']}\n"
        f"Duration: {context.user_data['duration']}\n"
        f"Purpose: {purpose}"
    )

    await update.message.reply_text(booking_details)
    await application.bot.send_message(chat_id=GROUP_CHAT_ID, text=booking_details, message_thread_id=MESSAGE_THREAD_ID)
    
    await update.message.reply_text("Your booking has been submitted. \nPlease look out for a confirmation message. Thank you.")
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Booking process cancelled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Create a conversation handler for creating bookings
create_booking_handler = ConversationHandler(
    entry_points=[CommandHandler('create_booking', create_booking)],
    states={
        ASK_BUTTERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_buttery)],
        ASK_DATE: [MessageHandler(filters.TEXT, ask_date)],
        ASK_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_time)],
        ASK_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_duration)],
        ASK_PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_purpose)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

# Add the conversation handler to the application
application.add_handler(create_booking_handler)

@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = Update.de_json(json_str, application.bot)
    application.process_update(update)
    return 'ok'

if __name__ == '__main__':
    application.run_polling()