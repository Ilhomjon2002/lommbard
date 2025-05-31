import requests
import time

TOKEN = "7552038732:AAFfh1uNfXBQsdSMDi-BayWFYRCzF9vx5Co"
ADMIN_ID = 1977657343  # Call-markaz adminining Telegram ID si
URL = f"https://api.telegram.org/bot{TOKEN}"

# Xabarlarni bog‘lash uchun dictionary
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

def main():
    last_update_id = None

    while True:
        updates = get_updates(last_update_id)
        if "result" in updates:
            for update in updates["result"]:
                last_update_id = update["update_id"] + 1
                
                # Foydalanuvchi xabari
                if "message" in update:
                    message = update["message"]
                    chat_id = message["chat"]["id"]
                    text = message.get("text", "")

                    # Agar foydalanuvchi /start bosgan bo‘lsa
                    if text == "/start":
                        send_welcome(chat_id)

                    # Agar foydalanuvchi yangi xabar yuborsa
                    elif chat_id != ADMIN_ID:
                        sent_msg = requests.post(f"{URL}/sendMessage", data={"chat_id": ADMIN_ID, "text": f"👤 ID: {chat_id}\n📝 Xabar: {text}"})
                        sent_msg_id = sent_msg.json().get("result", {}).get("message_id")
                        
                        if sent_msg_id:
                            user_messages[sent_msg_id] = chat_id  # Xabarni dictionary ga qo‘shamiz

                    # Agar admin reply qilib xabar yuborsa
                    elif chat_id == ADMIN_ID and "reply_to_message" in message:
                        reply_msg_id = message["reply_to_message"]["message_id"]

                        if reply_msg_id in user_messages:
                            user_id = user_messages[reply_msg_id]
                            send_message(user_id, f"📩 Call-markaz: {text}")
                            send_message(ADMIN_ID, "✅ Xabar foydalanuvchiga yuborildi!")
                        else:
                            send_message(ADMIN_ID, "⚠️ Bu xabarni foydalanuvchiga yuborib bo‘lmaydi.")

        time.sleep(1)  # Serverni zo‘riqtirmaslik uchun kutish

if __name__ == "__main__":
    main()
