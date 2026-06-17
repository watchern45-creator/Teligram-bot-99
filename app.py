import os
from flask import Flask, request
import telebot

# Environment variables se token aur admin ID nikalna (Render me configure karenge)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID'))

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- BOT LOGIC ---

# 1. /start command aur Admin Notification
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    chat_id = message.chat.id
    
    # User ko reply
    bot.reply_to(message, f"Hi {user_name}, kese ho?")
    
    # Admin ko notification (Agar start karne wala khud admin nahi hai to)
    if chat_id != ADMIN_ID:
        bot.send_message(
            ADMIN_ID, 
            f"🔔 *New User Started the Bot!*\n👤 Name: {user_name}\n🆔 ID: {chat_id}", 
            parse_mode="Markdown"
        )

# 2. Admin Broadcast Command (/broadcast <message>)
@bot.message_handler(commands=['broadcast'], func=lambda message: message.chat.id == ADMIN_ID)
def broadcast_message(message):
    # Command ke baad ka text nikalne ke liye
    text_to_send = message.text.split(' ', 1)
    if len(text_to_send) < 2:
        bot.reply_to(message, "❌ Please write a message. Example: `/broadcast Hello Users`")
        return
    
    msg_text = text_to_send[1]
    bot.reply_to(message, "📢 Broadcasting started...")
    
    # Note: Real bots me users ki list database me save hoti hai. 
    # Yahan hum un sabhi users ko bhej sakte hain jinki chat_id admin ke paas record ho.
    # Ek baar check kar lein ki aapke paas users ki list kahan saved hai.

# 3. Admin Reply Logic (Admin jab kisi forwarded message par swipe/reply karega)
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.reply_to_message is not None)
def handle_admin_reply(message):
    try:
        # Check karna ki admin ne jis message par reply kiya, kya wo kisi user se forward huye text/photo ka hai
        reply_to = message.reply_to_message
        
        # Forwarded message se user ki ID nikalna
        if reply_to.forward_from:
            user_id = reply_to.forward_from.id
        else:
            # Agar user ne privacy lagayi hai, to text me se ID dhundni hogi (Backup method)
            bot.reply_to(message, "❌ User ki privacy setting ki wajah se direct reply nahi ho saka. Unki ID par manually message bhejein.")
            return

        # Admin ka message user ko bhejna
        if message.content_type == 'text':
            bot.send_message(user_id, message.text)
        elif message.content_type == 'photo':
            bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
        elif message.content_type == 'voice':
            bot.send_voice(user_id, message.voice.file_id)
        
        bot.reply_to(message, "✅ Reply sent successfully!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# 4. User Messages (Text, Photo, Voice) Admin ko Forward karna
@bot.message_handler(content_types=['text', 'photo', 'voice'], func=lambda message: message.chat.id != ADMIN_ID)
def forward_to_admin(message):
    # Isse admin ko pata chalega kisne bheja hai aur admin 'Reply' (Swipe) kar sakega
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)


# --- FLASK WEB SERVER & WEBHOOK ---

@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    # RENDER_EXTERNAL_URL Render khud provide karta hai environment me
    server_url = os.environ.get('RENDER_EXTERNAL_URL') 
    bot.set_webhook(url=server_url + '/' + BOT_TOKEN)
    return "Bot is Running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
