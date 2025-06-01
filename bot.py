import os
import requests
import time
from threading import Thread

# Muhit o'zgaruvchilaridan ma'lumotlarni olish
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
URL = f"https://api.telegram.org/bot{TOKEN}"

# Har bir mijoz uchun alohida chatni saqlash uchun dictionary
user_chats = {}  # {user_id: {"chat_id": admin_chat_id, "messages": []}}

def get_updates(offset=None):
    """Telegram serveridan yangi xabarlarni olish"""
    params = {"offset": offset, "timeout": 30}
    response = requests.get(f"{URL}/getUpdates", params=params)
    return response.json()

def send_message(chat_id, text, reply_to_message_id=None, parse_mode=None):
    """Xabar yuborish"""
    data = {"chat_id": chat_id, "text": text}
    if reply_to_message_id:
        data["reply_to_message_id"] = reply_to_message_id
    if parse_mode:
        data["parse_mode"] = parse_mode
    response = requests.post(f"{URL}/sendMessage", data=data)
    return response.json().get("result", {}).get("message_id") if response.status_code == 200 else None

def send_photo(chat_id, photo_url, caption=None):
    """Rasm jo'natish"""
    data = {"chat_id": chat_id, "photo": photo_url}
    if caption:
        data["caption"] = caption
    requests.post(f"{URL}/sendPhoto", data=data)

def send_document(chat_id, document_url, caption=None):
    """Hujjat jo'natish"""
    data = {"chat_id": chat_id, "document": document_url}
    if caption:
        data["caption"] = caption
    requests.post(f"{URL}/sendDocument", data=data)

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
                    
                    if "message" in update:
                        message = update["message"]
                        chat_id = message["chat"]["id"]
                        text = message.get("text", "")
                        user_first_name = message.get("from", {}).get("first_name", "Anonim")

                        # Agar foydalanuvchi /start bosgan bo'lsa
                        if text == "/start" and chat_id != ADMIN_ID:
                            send_welcome(chat_id)
                            if chat_id not in user_chats:
                                # Yangi chat uchun alohida xabar adminiga
                                initial_msg = f"👤 Yangi mijoz: {user_first_name} (ID: {chat_id})\n📝 Suhbat boshlandi!"
                                msg_id = send_message(ADMIN_ID, initial_msg, parse_mode="HTML")
                                if msg_id:
                                    user_chats[chat_id] = {"chat_id": msg_id, "messages": []}

                        # Agar foydalanuvchi yangi xabar yuborsa
                        elif chat_id != ADMIN_ID and chat_id in user_chats:
                            user_chat_id = user_chats[chat_id]["chat_id"]
                            new_msg = f"👤 {user_first_name} (ID: {chat_id}):\n📝 {text}"
                            msg_id = send_message(ADMIN_ID, new_msg, parse_mode="HTML", reply_to_message_id=user_chat_id)
                            if msg_id:
                                user_chats[chat_id]["messages"].append({"msg_id": msg_id, "text": text})

                        # Agar admin reply qilib xabar yuborsa
                        elif chat_id == ADMIN_ID and "reply_to_message" in message:
                            reply_msg_id = message["reply_to_message"]["message_id"]
                            reply_text = message["text"]

                            for user_id, chat_data in user_chats.items():
                                if chat_data["chat_id"] == reply_msg_id or reply_msg_id in [msg["msg_id"] for msg in chat_data["messages"]]:
                                    send_message(user_id, f"📩 {reply_text}")
                                    send_message(ADMIN_ID, "✅ Xabar foydalanuvchiga yuborildi!", reply_to_message_id=reply_msg_id)
                                    break
                            else:
                                send_message(ADMIN_ID, "⚠️ Bu xabarni foydalanuvchiga yuborib bo'lmaydi.", reply_to_message_id=reply_msg_id)

        except Exception as e:
            print(f"Xatolik yuz berdi: {e}")
            time.sleep(5)
        time.sleep(1)

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
    bot_thread = Thread(target=bot_logic)
    bot_thread.daemon = True
    bot_thread.start()
    keep_alive()
