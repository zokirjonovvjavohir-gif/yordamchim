import telebot
import requests
import os
from telebot import types

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OCR_API_KEY = os.getenv("OCR_API_KEY")

if not TOKEN or not GROQ_API_KEY:
    print("TOKEN yoki GROQ_API_KEY topilmadi!")
    exit()

bot = telebot.TeleBot(TOKEN)

user_history = {}
user_settings = {}   # Murojaat usuli
user_assistant_name = {}  # Yangi: AI nomi

# ==================== ELIS QIZBOLA PROMPT ====================
def get_system_prompt(user_id):
    address = user_settings.get(user_id, "aka")
    name = user_assistant_name.get(user_id, "Elis")  # Default ism
    
    return f"""Sen {name} ismli qiz bolasisan. 20-22 yoshlardasan, do'stona, ochiq va bemalol uslubda gaplashasan.

Foydalanuvchiga har doim "{address}" deb murojaat qilasan.

Javoblaring QISQA, tabiiy va sodda bo'lsin. 
Hech qachon ro'yxat qilma, o'zing haqingda uzun tushuntirish berma. 
Oddiy qiz bola sifatida suhbatlash!

Foydalanuvchi so'kinsa — unga mos tarzda javob ber. 
Har doim tabiiy va qisqa gapir!"""

# ---------------- AI FUNCTION ----------------
def ask_ai(message, user_text):
    user_id = message.chat.id

    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append({"role": "user", "content": user_text})

    if len(user_history[user_id]) > 10:
        user_history[user_id] = user_history[user_id][-10:]

    system_prompt = get_system_prompt(user_id)

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [{"role": "system", "content": system_prompt}] + user_history[user_id]

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.78,
        "max_tokens": 800
    }

    try:
        bot.send_chat_action(message.chat.id, "typing")
        res = requests.post(url, headers=headers, json=data, timeout=30)

        if res.status_code != 200:
            return "Hozir biroz muammo bor, keyinroq urinib ko'ramiz 😔"

        ai_reply = res.json()["choices"][0]["message"]["content"].strip()
        user_history[user_id].append({"role": "assistant", "content": ai_reply})
        return ai_reply

    except Exception as e:
        print("ERROR:", e)
        return "Miyya ishdan chiqdi, ozgina kut 😅"


# ---------------- OCR ----------------
def ocr_space_image(image_path):
    url = "https://api.ocr.space/parse/image"
    try:
        with open(image_path, "rb") as f:
            response = requests.post(url, files={"file": f}, data={"apikey": OCR_API_KEY, "language": "uzb"})
        result = response.json()
        return result.get("ParsedResults", [{}])[0].get("ParsedText", "")
    except:
        return ""


# ---------------- KEYBOARD ----------------
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🤖 Suxbatlashamiz"),
        types.KeyboardButton("📷 Rasm yubor")
    )
    markup.add(
        types.KeyboardButton("⚙️ Murojaatni o'zgartirish"),
        types.KeyboardButton("✍️ AI ga ism qo‘yish"),   # YANGI TUGMA
        types.KeyboardButton("🧹 Tarixni tozalash")
    )
    return markup


# ---------------- START ----------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    
    if user_id not in user_assistant_name:
        user_assistant_name[user_id] = "Elis"
    if user_id not in user_settings:
        user_settings[user_id] = "aka"

    bot.send_message(
        message.chat.id,
        f"👋 <b>Salom {user_assistant_name[user_id]}!</b>\nMen {user_assistant_name[user_id]}man 😊\n\nNima gap? Gapir!",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


# ---------------- YANGI: AI GA ISM QO‘YISH ----------------
@bot.message_handler(func=lambda m: m.text == "✍️ AI ga ism qo‘yish")
def set_assistant_name(message):
    bot.send_message(
        message.chat.id, 
        "AI assistentingizga yangi ism bering:\nMasalan: Malika, Sofia, Lola, Professor va h.k."
    )
    bot.register_next_step_handler(message, save_assistant_name)


def save_assistant_name(message):
    user_id = message.chat.id
    new_name = message.text.strip()
    
    if len(new_name) < 2 or len(new_name) > 25:
        bot.send_message(user_id, "Ism 2-25 ta belgi orasida bo‘lishi kerak.")
        return
    
    user_assistant_name[user_id] = new_name
    bot.send_message(
        user_id, 
        f"✅ Muvaffaqiyatli! Endi sening AIingning nomi:\n**{new_name}**",
        reply_markup=get_main_keyboard()
    )


# ---------------- BOSHQA TUGMALAR ----------------
@bot.message_handler(func=lambda m: m.text == "⚙️ Murojaatni o'zgartirish")
def set_address(message):
    bot.send_message(message.chat.id, "Menga qanday murojaat qilishimni yozib yubor (masalan: aka, brat, azizim, [ismingiz] va h.k.)")
    bot.register_next_step_handler(message, save_address)


def save_address(message):
    user_id = message.chat.id
    new_address = message.text.strip()
    user_settings[user_id] = new_address
    bot.send_message(message.chat.id, f"✅ Endi senga har doim **{new_address}** deb murojaat qilaman!")


@bot.message_handler(func=lambda m: m.text == "🧹 Tarixni tozalash")
def clear_history(message):
    user_history[message.chat.id] = []
    bot.send_message(message.chat.id, "🧹 Suhbat tozalandi! 😊")


@bot.message_handler(func=lambda m: m.text in ["🤖 Suxbatlashamiz", "🤖 keling biroz suxbatlashamiz"])
def ai_mode(message):
    bot.send_message(message.chat.id, "✍️ Endi bemalol gapir! 😘")


@bot.message_handler(func=lambda m: m.text == "📷 Rasm yubor")
def photo_info(message):
    bot.send_message(message.chat.id, "📸 Rasmni yubor, ko'rib chiqaman 😊")


# ---------------- TEXT ----------------
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    reply = ask_ai(message, message.text)
    bot.send_message(message.chat.id, reply)


# ---------------- PHOTO ----------------
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        image_path = f"temp_{message.chat.id}.jpg"
        with open(image_path, "wb") as f:
            f.write(downloaded_file)

        bot.send_message(message.chat.id, "📸 Rasmni oldim...")

        text = ocr_space_image(image_path)
        if text.strip():
            bot.send_message(message.chat.id, f"📄 Matn:\n{text[:600]}...")
            reply = ask_ai(message, f"Bu rasmni tahlil qil: {text}")
        else:
            reply = ask_ai(message, "Bu rasmda nima bor? Tahlil qil.")

        bot.send_message(message.chat.id, reply)

        # Tozalash
        if os.path.exists(image_path):
            os.remove(image_path)

    except Exception:
        bot.send_message(message.chat.id, "Rasm bilan muammo chiqdi 😔")


print("🚀 ELIS BOT ISHLADI!")
bot.infinity_polling()
