import telebot
import requests
import os

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

print("TOKEN:", TOKEN)
print("GROQ:", GROQ_API_KEY)

if not TOKEN:
    print("TOKEN YO‘Q!")
    exit()

bot = telebot.TeleBot(TOKEN)

def ask_ai(text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
     "model": "llama-3.1-8b-instant",
        "messages": [
        {
            "role": "system",
            "content": "Sen o‘zbek tilida juda aniq, tushunarli va kocha tilida sokinib 
