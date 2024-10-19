from supabase_client import supabase
from datetime import datetime, timezone, timedelta

app_instance = None
group_chat_id = None
message_thread_id = None

SGT = timezone(timedelta(hours=8))

# Constants for repeated strings
TEAM_REMINDER_MSG = "Hi Buttery Booking team! This is your hourly reminder."
NO_BOOKINGS_MSG = "There are <u>no</u> unprocessed bookings at the moment."
USER_REMINDER_PREFIX = "Hi @{},"  # For user reminder prefix
BOOKING_REMINDER_MSG = (
    "Buttery: <b>{}</b>\n"
    "Date: {}\n"
    "Time: {}\n"
    "Duration: {}\n"
    "Purpose: {}"
)

def set_application_reminder(application, chat_id, thread_id):
    global app_instance, group_chat_id, message_thread_id
    app_instance = application
    group_chat_id = chat_id
    message_thread_id = thread_id

async def send_reminders(context):
    # Fetch bookings for the next hour
    response = supabase.table("Unprocessed Booking Request").select("*").execute()

    if response.data:
        await send_team_reminder(len(response.data))
        now = datetime.now(SGT)
        one_hour_later = now + timedelta(hours=1)
        for count, booking in enumerate(response.data, start=1):
            await send_group_reminder(booking, count)
            
            booking_datetime_str = booking['datetime']
            booking_datetime = datetime.fromisoformat(booking_datetime_str)
            if now <= booking_datetime <= one_hour_later: await send_user_reminder(booking)
    else:
        await send_no_bookings_reminder()

async def send_team_reminder(unprocessed_count):
    await app_instance.bot.send_message(
        chat_id=group_chat_id,
        text=f"{TEAM_REMINDER_MSG} You have {unprocessed_count} unprocessed {'booking' if unprocessed_count == 1 else 'bookings'}.",
        message_thread_id=message_thread_id,
        parse_mode='HTML'
    )

async def send_user_reminder(booking):
    telehandle = booking['telehandle']
    userChatId = booking['userChatID']
    
    booking_datetime = datetime.fromisoformat(booking['datetime'])
    booking_date = booking_datetime.strftime("%d/%m/%Y")
    booking_time = booking_datetime.strftime("%H%M")
    
    booking_details = format_booking_details(booking, booking_date, booking_time)

    await app_instance.bot.send_message(
        chat_id=userChatId,
        text=f"{USER_REMINDER_PREFIX.format(telehandle)} just a reminder for your upcoming buttery booking!\n\n{booking_details}",
        parse_mode='HTML'
    )

async def send_group_reminder(booking, count):
    booking_datetime = datetime.fromisoformat(booking['datetime'])
    booking_date = booking_datetime.strftime("%d/%m/%Y")
    booking_time = booking_datetime.strftime("%H%M")
    
    booking_details = format_booking_details(booking, booking_date, booking_time)

    await app_instance.bot.send_message(
        chat_id=group_chat_id,
        text=f"Unprocessed booking {count}: \n\nBooking request by @{booking['telehandle']}\n{booking_details}",
        message_thread_id=message_thread_id,
        parse_mode='HTML'
    )

def format_booking_details(booking, booking_date, booking_time):
    return BOOKING_REMINDER_MSG.format(
        booking['buttery'], 
        booking_date, 
        booking_time, 
        str(booking['duration']) + (" hour" if booking['duration'] == 1 else " hours"), 
        booking['purpose']
    )

async def send_no_bookings_reminder():
    await app_instance.bot.send_message(
        chat_id=group_chat_id,
        text=f"{TEAM_REMINDER_MSG} {NO_BOOKINGS_MSG}",
        message_thread_id=message_thread_id,
        parse_mode='HTML'
    )
