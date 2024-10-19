from telegram.ext import CommandHandler
from supabase_client import supabase
from datetime import datetime

async def list_bookings(update, context):
    telehandle = update.message.from_user.username
    response = supabase.table("Unprocessed Booking Request").select("*").eq("telehandle", telehandle).execute()
    bookings = response.data
    
    if not bookings:
        await update.message.reply_text("You have no bookings.")
        return
    
    booking_messages = [
    f"Buttery: <b>{b['buttery']}</b>\n"
    f"Date: {datetime.fromisoformat(b['datetime']).strftime('%d/%m/%Y')}\n"
    f"Time: {datetime.fromisoformat(b['datetime']).strftime('%H%M')}\n"
    f"Duration: {b['duration']} hours\n"
    f"Purpose: {b['purpose']}"
    for b in bookings
    ]
    
    
    await update.message.reply_text(f"You have <b>{len(booking_messages)}</b> bookings!\n\n" + "\n\n".join(booking_messages), parse_mode='HTML')

list_bookings_handler = CommandHandler('list_bookings', list_bookings)
