import os
import requests
import time
from threading import Thread

# Muhit o'zgaruvchilaridan ma'lumotlarni olish
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
URL = f"https://api.telegram.org/bot{TOKEN}"

# Xabarlarni bog'lash uchun dictionary
user_messages = {}

def get_updates(offset=None):
    """Telegram serveridan yangi xabarlarni olish"""
    params = {"offset": offset, "timeout": 30}
    response = requests.get(f"{URL}/getUpdates", params=params)
    return response.json()

def send_message(chat_id, text, reply_to_message_id=None):
    """Xabar yuborish"""
    data = {"chat_id": chat_id, "text": text}
    if reply_to_message_id:
        data["reply_to_message_id"] = reply_to_message_id
    requests.post(f"{URL}/sendMessage", data=data)

def send_welcome(chat_id):
    """Mijoz /start bosganda unga xush kelibsiz xabarini yuborish"""
    welcome_text = "🤖 Assalomu alaykum!\n\nSizning savollaringizni call-markaz qabul qiladi va tez orada javob beradi. Xabaringizni yozing!"
    send_message(chat_id, welcome_text)

def bot_logic():
    """Botning asosiy logikasi"""
    last_update_id = None

    while True:
        try:
            updates = get_updates(last_update_id)
            if "result" in updates:
                for update in updates["result"]:
                    last_update_id = update["update_id"] + 1
                    
                    # Foydalanuvchi xabari
                    if "message" in update:
                        message = update["message"]
                        chat_id = message["chat"]["id"]
                        text = message.get("text", "")

                        # Agar foydalanuvchi /start bosgan bo'lsa
                        if text == "/start":
                            send_welcome(chat_id)

                        # Agar foydalanuvchi yangi xabar yuborsa
                        elif chat_id != ADMIN_ID:
                            sent_msg = requests.post(f"{URL}/sendMessage", data={"chat_id": ADMIN_ID, "text": f"👤 ID: {chat_id}\n📝 Xabar: {text}"})
                            sent_msg_id = sent_msg.json().get("result", {}).get("message_id")
                            
                            if sent_msg_id:
                                user_messages[sent_msg_id] = chat_id  # Xabarni dictionary ga qo'shamiz

                        # Agar admin reply qilib xabar yuborsa
                        elif chat_id == ADMIN_ID and "reply_to_message" in message:
                            reply_msg_id = message["reply_to_message"]["message_id"]

                            if reply_msg_id in user_messages:
                                user_id = user_messages[reply_msg_id]
                                send_message(user_id, f"📩 Call-markaz: {text}")
                                send_message(ADMIN_ID, "✅ Xabar foydalanuvchiga yuborildi!")
                            else:
                                send_message(ADMIN_ID, "⚠️ Bu xabarni foydalanuvchiga yuborib bo'lmaydi.")

        except Exception as e:
            print(f"Xatolik yuz berdi: {e}")
            time.sleep(5)  # Xatolik yuz bersa, 5 soniya kuting va qayta urining
        time.sleep(1)  # Serverni zo'riqtirmaslik uchun kutish

def keep_alive():
    """Railway uchun botni doimiy ishlashini ta'minlash"""
    port = int(os.getenv("PORT", 8000))
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Bot is running!")

    server = HTTPServer(("", port), Handler)
    print(f"Server {port} portida ishga tushdi")
    server.serve_forever()

if __name__ == "__main__":
    # Botni alohida threadda ishga tushirish
    bot_thread = Thread(target=bot_logic)
    bot_thread.daemon = True
    bot_thread.start()

    # HTTP serverni ishga tushirish (Railway talabi)
    keep_alive()
