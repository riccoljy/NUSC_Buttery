from flask import Flask, request
from telegram import Update
from telegram.ext import Application
from handlers.booking import create_booking_handler, set_application  # Import the set_application function
from handlers.list import list_bookings_handler
from handlers.cancel import cancel_handler
from config import API_TOKEN, GROUP_CHAT_ID, MESSAGE_THREAD_ID, setup_environment

# Initialize Flask and Telegram bot
app = Flask(__name__)
application = Application.builder().token(API_TOKEN).build()

# Pass the `application`, `GROUP_CHAT_ID`, and `MESSAGE_THREAD_ID` to handlers
set_application(application, GROUP_CHAT_ID, MESSAGE_THREAD_ID)

# Register Telegram bot handlers
application.add_handler(create_booking_handler)
application.add_handler(list_bookings_handler)
application.add_handler(cancel_handler)

@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = Update.de_json(json_str, application.bot)
    application.process_update(update)
    return 'ok'

if __name__ == '__main__':
    setup_environment()
    application.run_polling()
