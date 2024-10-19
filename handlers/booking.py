import re
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from datetime import datetime, timedelta, timezone
from supabase_client import supabase
from handlers.cancel import cancel_handler
from state import set_started_booking_process, is_booking_process_started


# Define conversation states
ASK_BUTTERY, ASK_DATE, ASK_DURATION, ASK_PURPOSE, ASK_TIME = range(5)
SGT = timezone(timedelta(hours=8))

# Define keyboard markups
reply_markup_buttery = ReplyKeyboardMarkup([["Saga Buttery", "Elm Buttery"]], one_time_keyboard=True, resize_keyboard=True)
reply_markup_duration = ReplyKeyboardMarkup([['1', '2', '3', '4']], one_time_keyboard=True, resize_keyboard=True)

bookingDetails = {}

app_instance = None
group_chat_id = None
message_thread_id = None

def set_application_booking(application, chat_id, thread_id):
    global app_instance, group_chat_id, message_thread_id
    app_instance = application
    group_chat_id = chat_id
    message_thread_id = thread_id

async def create_booking(update, context) -> int:
    await update.message.reply_text(
        "Hey! Which buttery would you like to book?\n\n(Step 1 of 5)",
        reply_markup=reply_markup_buttery
    )
    set_started_booking_process(True)
    return ASK_BUTTERY

async def ask_buttery(update, context) -> int:
    chosen_buttery = update.message.text

    # Validate the chosen buttery
    if chosen_buttery not in ["Saga Buttery", "Elm Buttery"]:
        await update.message.reply_text(
            "Please select a valid buttery.",
            reply_markup=reply_markup_buttery
        )
        return ASK_BUTTERY
    
    context.user_data['chosen_buttery'] = chosen_buttery
    bookingDetails["buttery"] = chosen_buttery #9 if chosen_buttery == "Saga Buttery" else 11
    await ask_for_date(update, context)
    return ASK_DATE

async def ask_for_date(update, context) -> None:
    today = datetime.now(SGT).strftime("%d/%m/%Y")
    max_date = (datetime.now(SGT) + timedelta(days=30)).strftime("%d/%m/%Y")

    await update.message.reply_text(
        f"What date would you like to book the "
        f"<b>{bookingDetails['buttery']}</b>?\n"
        #{'Saga' if bookingDetails['buttery'] == 9 else 'Elm'} Buttery? \n"
        f"Send date in DD/MM/YYYY format, or /today or /tomorrow.\n\n"
        f"Date must be between {today} and {max_date}.\n\n(Step 2 of 5)",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='HTML'
    )

async def ask_date(update, context) -> int:
    date_str = update.message.text

    # Handle /today and /tomorrow commands
    if date_str in ["/today", "/tomorrow"]:
        selected_date = datetime.now(SGT).replace(hour=0, minute=0, second=0, microsecond=0)
        if date_str == "/tomorrow":
            selected_date += timedelta(days=1)
        
        context.user_data['booking_date'] = selected_date.strftime("%d/%m/%Y")
        bookingDetails["date"] = selected_date.strftime("%d/%m/%Y")
        await update.message.reply_text(f"Your booking has been selected for <b>{date_str[1:]} ({bookingDetails['date']}</b>).", parse_mode='HTML')
        await update.message.reply_text("What time is your does your booking start? \n\nPlease enter time in HHMM format in 30 min intervals (eg: 0700 or 2130).\n\n(Step 3 of 5)")
        return ASK_TIME

    # Validate normal date input
    try:
        date_obj = datetime.strptime(date_str, "%d/%m/%Y").replace(tzinfo=SGT)
        today = datetime.now(SGT).replace(hour=0, minute=0, second=0, microsecond=0)
        max_date = today + timedelta(days=30)
        
        if today <= date_obj <= max_date:
            date_obj = date_obj.strftime("%d/%m/%Y")
            context.user_data['booking_date'] = date_str
            bookingDetails["date"] = date_str
            await update.message.reply_text("What time is your does your booking start? \n\nPlease enter time in HHMM format in 30 min intervals (eg: 0700 or 2130).\n\n(Step 3 of 5)")
            return ASK_TIME
        else:
            await update.message.reply_text(f"Please enter a valid date between today and one month from now (between {today.strftime('%d/%m/%Y')} and {max_date.strftime('%d/%m/%Y')}). ")
            return ASK_DATE
    except ValueError:
        await update.message.reply_text("Invalid date format. Please send the date in DD/MM/YYYY format.")
        return ASK_DATE
    
async def ask_time(update, context) -> int:
    time_input = update.message.text
    
    # Regular expression to match valid HHMM format with minutes being 00 or 30
    time_format = re.compile(r"^([01]\d|2[0-3])(00|30)$")
    
    if time_format.match(time_input):
        booking_time = datetime.strptime(time_input, "%H%M").time()
        now = datetime.now(SGT)
        current_time = now.time()
        input_date = datetime.strptime(context.user_data['booking_date'], "%d/%m/%Y").date()
        if input_date == now.date() and booking_time < current_time:
            await update.message.reply_text(
                "You can't book for a time that has passed.......... Please enter a valid time...",
                reply_markup=ReplyKeyboardRemove()
            )
            return ASK_TIME
        context.user_data['booking_time'] = time_input
        bookingDetails["time"] = time_input
        await update.message.reply_text(
            "How long is your booking? (Please select a time range of 1 to 4 hours)\n\n(Step 4 of 5)",
            reply_markup=reply_markup_duration
        )
        return ASK_DURATION
    else: # Invalid time format, prompt user to enter again
        await update.message.reply_text(
            "Invalid time format. Please enter time in HHMM format in 30 min intervals (eg: 0700 or 2130).",
            reply_markup=ReplyKeyboardRemove()
        )
        return ASK_TIME


async def ask_duration(update, context) -> int:
    try:
        duration = float(update.message.text)
        if 1 <= duration <= 4:
            context.user_data['duration'] = duration
            bookingDetails['duration'] = duration
            await update.message.reply_text("What is the purpose of this booking?\n\n(Step 5 of 5)", reply_markup=ReplyKeyboardRemove())
            return ASK_PURPOSE
        else:
            await update.message.reply_text("Please select a duration between 1 and 4 hours.", reply_markup=reply_markup_duration)
            return ASK_DURATION
    except ValueError:
        await update.message.reply_text("Please select a valid number for the duration of booking.")
        return ASK_DURATION

async def ask_purpose(update, context) -> int:
    purpose = update.message.text
    context.user_data['purpose'] = purpose
    bookingDetails['purpose'] = purpose
    telehandle = update.message.from_user.username
    userId = update.message.from_user.id
    
    date_str = bookingDetails['date']
    time_str = bookingDetails['time']
    booking_datetime = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H%M").replace(tzinfo=SGT)

    booking_details = (
        f"Booking Request by @{telehandle}:\n"
        f"Buttery: {bookingDetails['buttery']}\n"
        f"Date: {date_str}\n"
        f"Time: {time_str}\n"
        f"Duration: {str(bookingDetails['duration']) + (' hour' if bookingDetails['duration'] == 1 else ' hours')}\n"
        f"Purpose: {purpose}"
    )
    
    supabase.table("Unprocessed Booking Request").insert({
        "telehandle": telehandle,
        "userChatID": userId,
        "buttery": bookingDetails['buttery'],
        "datetime": booking_datetime.isoformat(),
        "duration": bookingDetails['duration'],
        "purpose": purpose
    }).execute()

    await update.message.reply_text(booking_details)
    await app_instance.bot.send_message(chat_id=group_chat_id, text=f"Hi my beloved booking ICs, you have a NEW booking!🥰🥰\n\n{booking_details}", message_thread_id=message_thread_id)
    await update.message.reply_text("Your booking has been submitted. \nPlease look out for a confirmation message. Thank you.")
    return ConversationHandler.END

# ConversationHandler for bookings
create_booking_handler = ConversationHandler(
    entry_points=[CommandHandler('create_booking', create_booking)],
    states={
        ASK_BUTTERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_buttery)],
        ASK_DATE: [MessageHandler(filters.TEXT, ask_date)],
        ASK_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_time)],
        ASK_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_duration)],
        ASK_PURPOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_purpose)],
    },
    fallbacks=[cancel_handler]
)
