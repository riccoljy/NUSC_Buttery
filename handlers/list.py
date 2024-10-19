from telegram.ext import CommandHandler
from supabase_client import supabase

async def list_bookings(update, context):
    telehandle = update.message.from_user.username
    response = supabase.table("Unprocessed Booking Request").select("*").eq("telehandle", telehandle).execute()
    bookings = response.data
    
    if not bookings:
        await update.message.reply_text("You have no bookings.")
        return

    booking_messages = [f"Buttery: {b['buttery']}\nDate: {b['date']}\nTime: {b['time']}\nDuration: {b['duration']} hours\nPurpose: {b['purpose']}" for b in bookings]
    await update.message.reply_text("\n\n".join(booking_messages))

list_bookings_handler = CommandHandler('list_bookings', list_bookings)
