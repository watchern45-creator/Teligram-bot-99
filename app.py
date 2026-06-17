import os
import sys
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Enable logging taaki Railway par live logs dikhein
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Fetch environment variables safely from Railway
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")  # Admin ki Telegram Chat ID

if not TOKEN or not ADMIN_ID:
    print("❌ ERROR: BOT_TOKEN ya ADMIN_ID Environment Variables me nahi mila!")
    sys.exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start command handler"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # User ko reply dena
    await update.message.reply_text(f"Hi {user.first_name}, kese ho? 😊")
    
    # Admin ko notification bhejna
    if str(chat_id) != str(ADMIN_ID):
        notification = (
            f"🔔 **New User Started the Bot!**\n"
            f"👤 Name: {user.first_name}\n"
            f"🆔 ID: {chat_id}\n"
            f"Username: @{user.username if user.username else 'None'}"
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=notification, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Admin ko notification bhejne me error: {e}")

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ke messages Admin ko bhejna aur Admin ka reply Swipe/Reply se user tak pahunchana"""
    chat_id = update.effective_chat.id
    message = update.message

    if not message:
        return

    # 1. AGAR ADMIN REPLY KAR RAHA HAI (Swipe / Reply Feature)
    if str(chat_id) == str(ADMIN_ID) and message.reply_to_message:
        # Reply wale message ka text ya caption check karenge target ID dhoodhne ke liye
        reply_text = message.reply_to_message.text or message.reply_to_message.caption
        if reply_text and "User ID:" in reply_text:
            try:
                # Text me se User ID nikalna
                target_user_id = reply_text.split("User ID:")[1].strip().split("\n")[0]
                
                # Admin ka reply user ko send karna
                if message.text:
                    await context.bot.send_message(chat_id=target_user_id, text=message.text)
                elif message.photo:
                    await context.bot.send_photo(chat_id=target_user_id, photo=message.photo[-1].file_id, caption=message.caption)
                elif message.voice:
                    await context.bot.send_voice(chat_id=target_user_id, voice=message.voice.file_id, caption=message.caption)
                
                await message.reply_text("✅ Reply user tak pahunch gaya!")
                return
            except Exception as e:
                await message.reply_text(f"❌ Reply bhejne me dikkat aayi: {e}")
                return

    # 2. AGAR USER NE KUCH BHEJA HAI (Admin tak forward karna)
    if str(chat_id) != str(ADMIN_ID):
        user_info = f"\n\nFrom: {update.effective_user.first_name}\nUser ID: {chat_id}"
        
        try:
            if message.text:
                await context.bot.send_message(chat_id=ADMIN_ID, text=f"💬 **New Message:**\n{message.text}{user_info}")
            elif message.photo:
                await context.bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=f"📸 **New Photo**{user_info}")
            elif message.voice:
                await context.bot.send_voice(chat_id=ADMIN_ID, voice=message.voice.file_id, caption=f"🎙️ **New Voice**{user_info}")
        except Exception as e:
            logger.error(f"Admin ko forward karne me error: {e}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin sabhi users ko ek sath message bhej sakta hai"""
    if str(update.effective_chat.id) != str(ADMIN_ID):
        return

    if not context.args:
        await update.message.reply_text("❌ Format: `/broadcast Aapka Message`", parse_mode="Markdown")
        return

    broadcast_msg = " ".join(context.args)
    await update.message.reply_text(f"📢 Broadcast command received!\n\nMessage: {broadcast_msg}\n\n*(Note: Pure broadcast ke liye database list lagti hai, abhi aap manual swipe reply se sabhi active users ko message bhej sakte hain!)*")

def main():
    print("🚀 Starting Bot on Railway...")
    
    # Build application (Stable Long Polling)
    application = Application.builder().token(TOKEN).build()

    # Handlers Add karna
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.VOICE, handle_messages))

    # Run polling (Railway auto-detects and runs this 24/7)
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
