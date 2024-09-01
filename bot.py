from flask import Flask, request
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from dotenv import load_dotenv
import requests
import os

# Load environment variables from .env file
load_dotenv()

# DB Info
# SUPABASE_URL = os.getenv("EXPO_PUBLIC_SUPABASE_URL")
# SUPABASE_KEY = os.getenv("EXPO_PUBLIC_SUPABASE_ANON_KEY")

app = Flask(__name__)

# Get the API token from environment variable
API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
print('token = ', API_TOKEN)

updater = Updater(API_TOKEN)
dispatcher = updater.dispatcher

# Define conversation states
ASK_NUSNET_ID, ASK_BOOKING_DETAILS = range(2)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Let's start linking your account for booking the Buttery!\n"
        "If you don't wish to continue, click /cancel\n"
        "Please enter your NUSNET ID:",
    )
    return ASK_NUSNET_ID

def ask_nusnet_id(update: Update, context: CallbackContext) -> None:
    context.user_data['nusnet_id'] = update.message.text
    update.message.reply_text(
        "NUSNET ID received. If you don't wish to continue, click /cancel\n"
        "Now, please provide the booking details (e.g., date, time, duration):",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASK_BOOKING_DETAILS

def ask_booking_details(update: Update, context: CallbackContext) -> None:
    booking_details = update.message.text
    nusnet_id = context.user_data.get('nusnet_id')
    update.message.reply_text(
        "Please hang on while we verify your account and process the booking."
    )

    # Attempt to verify NUSNET ID with Supabase
    # response = requests.post(
    #     f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
    #     headers={
    #         "apikey": SUPABASE_KEY,
    #         "Content-Type": "application/json"
    #     },
    #     json={
    #         "nusnet_id": nusnet_id
    #     }
    # )

    # if response.status_code == 200:
    #     data = response.json()
    #     access_token = data.get('access_token')
    #     user_id = data.get('user', {}).get('id')

    #     if access_token and user_id:
    #         telegram_id = update.message.from_user.id
    #         metadata_response = requests.put(
    #             f"{SUPABASE_URL}/auth/v1/user",
    #             headers={
    #                 "apikey": SUPABASE_KEY,
    #                 "Authorization": f"Bearer {access_token}",
    #                 "Content-Type": "application/json"
    #             },
    #             json={
    #                 "data": {"telegram_id": telegram_id}
    #             }
    #         )
    #         if metadata_response.status_code == 200:
    #             update.message.reply_text("Booking successful! Your account has been linked.")
    #         else:
    #             update.message.reply_text("Failed to update user metadata.")
    #     else:
    #         update.message.reply_text("Failed to retrieve user data.")
    # else:
        # update.message.reply_text("Booking failed. Please check your NUSNET ID. Click /book again once you are ready to book the Buttery.")
    update.message.reply_text("Sorry we actually havent finished lol")

    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Booking process cancelled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Create a conversation handler with the states ASK_NUSNET_ID and ASK_BOOKING_DETAILS
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('book', start)],
    states={
        ASK_NUSNET_ID: [MessageHandler(Filters.text & ~Filters.command, ask_nusnet_id)],
        ASK_BOOKING_DETAILS: [MessageHandler(Filters.text & ~Filters.command, ask_booking_details)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

dispatcher.add_handler(conv_handler)

@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = Update.de_json(json_str, updater.bot)
    dispatcher.process_update(update)
    return 'ok'

if __name__ == '__main__':
    updater.start_polling()
    port = int(os.environ.get("PORT", 5000))  # Use the PORT environment variable
    app.run(host='0.0.0.0', port=port)
