import telebot
import os
from dotenv import load_dotenv
import sqlalchemy as sq
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Word, create_tables

load_dotenv()
token = os.getenv('token')
DSN = os.getenv('DSN')

engine = create_engine(DSN)
bot = telebot.TeleBot(token)
create_tables(engine)
Session = sessionmaker(bind=engine)

@bot.message_handler(commands=['start'])
def start(message):
    cid = message.chat.id
    username = message.from_user.username
    with Session() as session:
        user = session.query(User).filter(User.cid == cid).first()
        if user:
            bot.send_message(chat_id=cid, text=f"Привет! Приятно тебя снова видеть здесь)")
        else:
            try:
                obj = User(cid=cid, username=username)
                session.add(obj)
                session.commit()
                bot.send_message(chat_id=cid, text=f"Привет, приятно познакомиться")
            except Exception as e:
                print(e)
                session.rollback()

if "__main__" == __name__:
    print("Bot working...")
    bot.polling()