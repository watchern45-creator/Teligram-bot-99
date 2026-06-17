import os
import logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Bot Zinda Hai!"

@flask_app.route("/health")
def health():
    return {"status": "ok"}, 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or "Dost"
    await update.message.reply_text(f"Hi {name}! Kese ho?")
    context.bot_data.setdefault("all_users", set()).add(user.id)
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Naya User Aaya!\nNaam: {user.full_name}\nID: {user.id}\nUsername: @{user.username or 'N/A'}"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == ADMIN_ID:
        return
    context.bot_data.setdefault("all_users", set()).add(user.id)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Reply Karo", callback_data=f"reply_{user.id}")]])
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Message\nUser: {user.full_name} | {user.id}\n{update.message.text}",
        reply_markup=kb
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == ADMIN_ID:
        return
    context.bot_data.setdefault("all_users", set()).add(user.id)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Reply Karo", callback_data=f"reply_{user.id}")]])
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"Photo\nUser: {user.full_name} | {user.id}",
        reply_markup=kb
    )

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == ADMIN_ID:
        return
    context.bot_data.setdefault("all_users", set()).add(user.id)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Reply Karo", callback_data=f"reply_{user.id}")]])
    await context.bot.send_voice(
        chat_id=ADMIN_ID,
        voice=update.message.voice.file_id,
        caption=f"Voice\nUser: {user.full_name} | {user.id}",
        reply_markup=kb
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return
    target_id = int(query.data.split("_")[1])
    context.user_data["reply_to"] = target_id
    await query.message.reply_text(f"Ab message likho - User {target_id} ko jayega.")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    if text.startswith("/all "):
        msg = text[5:]
        all_users = context.bot_data.get("all_users", set())
        sent = 0
        for uid in all_users:
            try:
                await context.bot.send_message(chat_id=uid, text=msg)
                sent += 1
            except:
                pass
        await update.message.reply_text(f"{sent} users ko bheja!")
        return
    target = context.user_data.get("reply_to")
    if target:
        try:
            await context.bot.send_message(chat_id=target, text=text)
            await update.message.reply_text(f"User {target} ko reply gaya!")
            context.user_data.pop("reply_to", None)
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

def main():
    Thread(target=run_flask, daemon=True).start()
    logger.info("Flask chalu...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback, pattern=r"^reply_"))
    app.add_handler(MessageHandler(filters.User(ADMIN_ID) & filters.TEXT, handle_admin_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    logger.info("Bot chal raha hai...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
