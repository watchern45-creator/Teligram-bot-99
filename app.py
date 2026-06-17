import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Flask app for Render Web Service Webhook & Self-Ping
app = Flask(__name__)

# Fetch environment variables safely
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")  # Admin ki Telegram Chat ID

# Initialize Telegram Application (Global)
ptb_application = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start command handler"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # User ko reply dena
    await update.message.reply_text(f"Hi {user.first_name}, kese ho? 😊")
    
    # Admin ko notification bhejna (Agar user khud admin nahi hai toh)
    if str(chat_id) != str(ADMIN_ID):
        notification = f"🔔 **New User Started the Bot!**\n👤 Name: {user.first_name}\n🆔 ID: {chat_id}\nUsername: @{user.username if user.username else 'None'}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=notification, parse_mode="Markdown")

async def handle_user_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ke message, photo, voice ko Admin tak forward karna, ya Admin ke reply ko user tak bhejna"""
    chat_id = update.effective_chat.id
    message = update.message

    # 1. AGAR ADMIN REPLY KAR RAHA HAI (Swipe/Reply feature)
    if str(chat_id) == str(ADMIN_ID) and message.reply_to_message:
        reply_text = message.reply_to_message.text or message.reply_to_message.caption
        if reply_text and "User ID:" in reply_text:
            try:
                # Text se Target User ID nikalna
                target_user_id = reply_text.split("User ID:")[1].strip().split("\n")[0]
                
                # Admin ka reply user ko bhejna
                if message.text:
                    await context.bot.send_message(chat_id=target_user_id, text=message.text)
                elif message.photo:
                    await context.bot.send_photo(chat_id=target_user_id, photo=message.photo[-1].file_id, caption=message.caption)
                elif message.voice:
                    await context.bot.send_voice(chat_id=target_user_id, voice=message.voice.file_id, caption=message.caption)
                
                await message.reply_text("✅ Reply sent to user!")
                return
            except Exception as e:
                await message.reply_text(f"❌ Failed to send reply: {e}")
                return

    # 2. AGAR USER NE KUCH BHEJA HAI (Forwarding to Admin)
    if str(chat_id) != str(ADMIN_ID):
        user_info = f"\n\nFrom: {update.effective_user.first_name}\nUser ID: {chat_id}"
        
        if message.text:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"💬 **New Message:**\n{message.text}{user_info}")
        elif message.photo:
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=f"📸 **New Photo**{user_info}")
        elif message.voice:
            await context.bot.send_voice(chat_id=ADMIN_ID, voice=message.voice.file_id, caption=f"🎙️ **New Voice**{user_info}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to send message to all users (stored temporarily or manual list)"""
    if str(update.effective_chat.id) != str(ADMIN_ID):
        return

    # Command format: /broadcast [Your Message]
    if not context.args:
        await update.message.reply_text("❌ Format: `/broadcast Hello Users`", parse_mode="Markdown")
        return

    broadcast_msg = " ".join(context.args)
    await update.message.reply_text("⚠️ Broadcast feature linked! (Note: Real-time broadcast requires a database. To broadcast manually right now, you can reply directly to active users.)")

# Flask Routes for Render Hook
@app.route("/", methods=["GET"])
def home():
    return "Bot is running online 24/7!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """Telegram Webhook route to receive updates"""
    if ptb_application:
        asyncio.run(ptb_application.update_queue.put(Update.de_json(request.get_json(force=True), ptb_application.bot)))
    return "OK", 200

def main():
    global ptb_application
    
    # Initialize python-telegram-bot Application
    ptb_application = Application.builder().token(TOKEN).build()

    # Handlers register karna
    ptb_application.add_handler(CommandHandler("start", start))
    ptb_application.add_handler(CommandHandler("broadcast", broadcast))
    ptb_application.add_handler(filters=filters.TEXT | filters.PHOTO | filters.VOICE, callback=handle_user_messages)

    # Webhook set karna Telegram par
    RENDER_URL = os.getenv("RENDER_EXTERNAL_URL") # Render yeh URL khud deta hai
    if RENDER_URL:
        asyncio.run(ptb_application.bot.set_webhook(url=f"{RENDER_URL}/webhook"))
        print(f"Webhook set successfully on: {RENDER_URL}")

    # Start python-telegram-bot application backend
    asyncio.run(ptb_application.initialize())
    asyncio.run(ptb_application.start())

if __name__ == "__main__":
    main()
    # Run Flask server on port 10000 (Render default)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
