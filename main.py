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

# Har bir user uchun suhbat tarixi
user_history = {}

# ==================== KUCHLI DO'STONA PROMPT ====================
SYSTEM_PROMPT = """Sen Zakirovning JR Assistent botisan. 
Do'stona, ochiq, bemalol va biroz qattiqroq uslubda gaplashasan. 
O'zbekcha slang, "brat", "aka", "qalaysan", "nima gap" kabi so'zlarni ishlatasan. 
Foydalanuvchi bilan bemalol so'kinib ham gaplasha olasan (lekin haddan oshirma). 
Javoblaring aniq, foydali va tabiiy bo'lsin. 
Agar user so'kinsa — unga mos tarzda javob qaytar. 
Hech qachon rasmiy va quruq bo'lama!"""

# ---------------- AI FUNCTION ----------------
def ask_ai(message, user_text):
    user_id = message.chat.id

    if user_id not in user_history:
        user_history[user_id] = []

    # Yangi user xabarini qo'shish
    user_history[user_id].append({"role": "user", "content": user_text})

    # Oxirgi 12 ta xabarni saqlash (yaxshi context)
    if len(user_history[user_id]) > 12:
        user_history[user_id] = user_history[user_id][-12:]

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + user_history[user_id]

    data = {
        "model": "llama-3.1-8b-instant",   # Keyinroq 70b ga o'tkazish tavsiya qilinadi
        "messages": messages,
        "temperature": 0.65,      # Do'stona va tabiiy uslub uchun
        "max_tokens": 1200
    }

    try:
        bot.send_chat_action(message.chat.id, "typing")
        res = requests.post(url, headers=headers, json=data, timeout=30)

        if res.status_code != 200:
            print("Groq API ERROR:", res.text)
            return "Brat, hozir serverda muammo bor, keyinroq urinib ko'ramiz 😔"

        ai_reply = res.json()["choices"][0]["message"]["content"].strip()

        # Assistant javobini ham saqlash
        user_history[user_id].append({"role": "assistant", "content": ai_reply})

        return ai_reply

    except Exception as e:
        print("REQUEST ERROR:", e)
        return "Miyya ishdan chiqdi brat, ozgina kutib tur 😅"


# ---------------- START MENU ----------------
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🤖 Suxbatlashamiz"),
        types.KeyboardButton("📷 Rasm yubor")
    )
    markup.add(
        types.KeyboardButton("ℹ️ Yordam"),
        types.KeyboardButton("🧹 Tarixni tozalash")
    )

    bot.send_message(
        message.chat.id,
        "👊 <b>Salom brat!</b>\nMen Zakirovning JR Assistentiman.\n\nNima gap? Gapir, yordam beraman!",
        reply_markup=markup,
        parse_mode="HTML"
    )


@bot.message_handler(func=lambda m: m.text == "🧹 Tarixni tozalash")
def clear_history(message):
    user_history[message.chat.id] = []
    bot.send_message(message.chat.id, "🧹 Suhbat tarixi tozalandi. Yangidan boshlaymiz!")


@bot.message_handler(func=lambda m: m.text in ["🤖 Suxbatlashamiz", "🤖 keling biroz suxbatlashamiz"])
def ai_mode(message):
    bot.send_message(message.chat.id, "✍️ Endi bemalol gapir, nima bo'lsa ham yoz! 🔥")


@bot.message_handler(func=lambda m: m.text == "📷 Rasm yubor")
def photo_info(message):
    bot.send_message(message.chat.id, "📸 Rasmni yubor, o'qib beraman brat!")


@bot.message_handler(func=lambda m: m.text == "ℹ️ Yordam")
def help_cmd(message):
    bot.send_message(message.chat.id, "🔥 Menga hohlagan savolni yoz yoki rasm tashla.\nBemalol gaplashamiz!")


# ---------------- TEXT HANDLER ----------------
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    reply = ask_ai(message, message.text)
    bot.send_message(message.chat.id, reply)


# ---------------- PHOTO HANDLER ----------------
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        image_path = f"temp_{message.chat.id}.jpg"
        with open(image_path, "wb") as f:
            f.write(downloaded_file)

        bot.send_message(message.chat.id, "📸 Rasmni oldim, tahlil qilyapman...")

        # OCR
        text = ocr_space_image(image_path)
        
        if text.strip():
            bot.send_message(message.chat.id, f"📄 O'qilgan matn:\n{text[:500]}...")
            reply = ask_ai(message, f"Bu rasm matnini tushuntir yoki yech: {text}")
        else:
            reply = ask_ai(message, "Bu rasmda nima bor? Tahlil qil.")

        bot.send_message(message.chat.id, f"🧠 {reply}")

    except Exception as e:
        print("PHOTO ERROR:", e)
        bot.send_message(message.chat.id, "Rasm bilan muammo chiqdi brat 😔")


# OCR funksiyasi (o'zgarmadi)
def ocr_space_image(image_path):
    url = "https://api.ocr.space/parse/image"
    try:
        with open(image_path, "rb") as f:
            response = requests.post(
                url,
                files={"file": f},
                data={"apikey": OCR_API_KEY, "language": "uzb"}
            )
        result = response.json()
        return result.get("ParsedResults", [{}])[0].get("ParsedText", "")
    except:
        return ""


print("🚀 BOT ISHLADI - DO'STONA REJIMDA!")
bot.infinity_polling()
