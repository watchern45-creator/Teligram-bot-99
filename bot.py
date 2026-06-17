import os
import logging
from keep_alive import keep_alive
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)

# ✅ Render me Environment Variables set karo (GitHub me mat daalo)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ✅ /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_name = user.first_name or "Dost"

    # User ko greeting
    await update.message.reply_text(f"Hi {user_name}! Kese ho? 😊")

    # Admin ko notification
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"🔔 *Naya User Aaya!*\n\n"
            f"👤 Naam: {user.full_name}\n"
            f"🆔 User ID: `{user.id}`\n"
            f"📛 Username: @{user.username or 'N/A'}"
        ),
        parse_mode="Markdown"
    )

# ✅ User ka text message → Admin ko forward karo
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Admin ka message ignore karo (warna loop)
    if user.id == ADMIN_ID:
        return

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"💬 *Naya Message*\n\n"
            f"👤 {user.full_name} | `{user.id}`\n"
            f"📝 Message: {update.message.text}\n\n"
            f"_Reply karne ke liye is message ko swipe karke reply karo_"
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "↩️ Reply Karo",
                callback_data=f"reply_{user.id}"
            )]
        ])
    )

    # Admin ke forward message ka reply_to_message ID save karo
    context.bot_data.setdefault("user_messages", {})[user.id] = update.message.message_id

# ✅ User ka photo → Admin ko forward
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == ADMIN_ID:
        return

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=(
            f"🖼️ *Photo Aayi!*\n"
            f"👤 {user.full_name} | `{user.id}`\n"
            f"{update.message.caption or ''}"
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Reply Karo", callback_data=f"reply_{user.id}")]
        ])
    )
    context.bot_data.setdefault("user_messages", {})[user.id] = update.message.message_id

# ✅ User ki voice → Admin ko forward
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == ADMIN_ID:
        return

    await context.bot.send_voice(
        chat_id=ADMIN_ID,
        voice=update.message.voice.file_id,
        caption=(
            f"🎙️ *Voice Message!*\n"
            f"👤 {user.full_name} | `{user.id}`"
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Reply Karo", callback_data=f"reply_{user.id}")]
        ])
    )
    context.bot_data.setdefault("user_messages", {})[user.id] = update.message.message_id

# ✅ Admin → Specific User ko reply (Inline button se)
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    target_user_id = int(query.data.split("_")[1])
    context.user_data["reply_to_user"] = target_user_id

    await query.message.reply_text(
        f"✏️ Ab apna reply message bhejo — User `{target_user_id}` ko jayega.",
        parse_mode="Markdown"
    )

# ✅ Admin ka message → User ko bhejo (ya /all se broadcast)
async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return

    # /all command: Sare users ko broadcast
    if update.message.text and update.message.text.startswith("/all "):
        broadcast_text = update.message.text[5:]
        all_users = context.bot_data.get("all_users", set())

        sent = 0
        for uid in all_users:
            try:
                await context.bot.send_message(chat_id=uid, text=f"📢 {broadcast_text}")
                sent += 1
            except Exception as e:
                logger.warning(f"User {uid} ko message nahi gaya: {e}")

        await update.message.reply_text(f"✅ {sent} users ko message bheja gaya!")
        return

    # Specific user ko reply
    target_user = context.user_data.get("reply_to_user")
    if target_user:
        try:
            await context.bot.send_message(
                chat_id=target_user,
                text=f"💬 {update.message.text}"
            )
            await update.message.reply_text(f"✅ User `{target_user}` ko reply bheja!", parse_mode="Markdown")
            context.user_data.pop("reply_to_user", None)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

# ✅ Sare users track karo
async def track_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user and user.id != ADMIN_ID:
        context.bot_data.setdefault("all_users", set()).add(user.id)

# ✅ Main function
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback, pattern=r"^reply_"))

    # Admin handlers
    app.add_handler(MessageHandler(
        filters.TEXT & filters.User(ADMIN_ID), handle_admin_message
    ))

    # User handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # User tracker (sabse pehle chale)
    app.add_handler(MessageHandler(filters.ALL, track_users), group=1)

    logger.info("✅ Bot chal raha hai...")
    keep_alive()  # Flask server start karo (Cron job ke liye)
    app.run_polling()

if __name__ == "__main__":
    main()
