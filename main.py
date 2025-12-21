import telebot
from dotenv import load_dotenv
import os
token = os.getenv('token')
bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет, со мной ты можешь выучить английские слова, Давай приступим!")