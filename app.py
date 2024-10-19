import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application
from datetime import datetime, timedelta
from handlers.booking import create_booking_handler, set_application, send_reminders   # Import the set_application function
from handlers.list import list_bookings_handler
from handlers.cancel import cancel_handler
from config import API_TOKEN, GROUP_CHAT_ID, MESSAGE_THREAD_ID, setup_environment

# Initialize Flask and Telegram bot
app = Flask(__name__)
application = Application.builder().token(API_TOKEN).build()

# Pass the `application`, `GROUP_CHAT_ID`, and `MESSAGE_THREAD_ID` to handlers
set_application(application, GROUP_CHAT_ID, MESSAGE_THREAD_ID)

# def run_send_reminders():
#     loop = asyncio.new_event_loop()  # Create a new event loop for the current thread
#     asyncio.set_event_loop(loop)     # Set the new loop as the current event loop
#     loop.run_until_complete(send_reminders())
#     loop.close()                     # Close the loop after the task completes


# Initialize a job_queue for periodic reminders
job_queue = application.job_queue

# Schedule the send_reminders function to run every hour
now = datetime.now()
next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
time_until_next_hour = (next_hour - now).total_seconds()
print(time_until_next_hour)
job_queue.run_repeating(send_reminders, interval=3600)

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
