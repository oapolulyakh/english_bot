import telebot
import os
from dotenv import load_dotenv
import sqlalchemy as sq
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, session
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

@bot.message_handler(commands=['add'])

def ask_word(message):
    msg = bot.send_message(chat_id=message.chat.id, text="Введите слово на английском языке")
    bot.register_next_step_handler(msg, ask_translation)

def ask_translation(message):
    cid = message.chat.id
    if message.content_type != 'text':
        msg = bot.send_message(cid, f"Это не текст. Введите слово буквами")
        bot.register_next_step_handler(msg, ask_translation)
        return
    word = message.text.strip().lower()
    msg = bot.send_message(cid, f'Введите перевод для слова "{word}"')
    bot.register_next_step_handler(msg, add_word_db, word)


def add_word_db(message, word):
    cid = message.chat.id

    if message.content_type != 'text':
        msg = bot.send_message(cid, f"Это не текст, введите перевод буквами")
        bot.register_next_step_handler(msg, add_word_db, word)
        return
    translation = message.text.strip().lower()

    try:
        with Session() as session:
            user = session.query(User).filter(User.cid == cid).first()
            if not user:
                bot.send_message(chat_id=cid, text= "Вы не авторизованы, введите /start")
                return

            existing_word = session.query(Word).filter(
                Word.word == word,
                Word.translation == translation,
                Word.user_id == user.id
                ).first()
            if existing_word:
                bot.send_message(chat_id=cid, text=f'Слово "{word}" с переводом "{translation}" уже есть в словаре')
            else:
                obj = Word(word=word, translation=translation, user_id=user.id)
                session.add(obj)
                session.commit()
                bot.send_message(chat_id=cid, text=f'Слово "{word}" с переводом "{translation}" добавлено')
    except Exception as e:
        print(e)
        bot.send_message(chat_id=cid, text="Что-то пошло не так при записи. Попробуй позже.")



if "__main__" == __name__:
    print("Bot working...")
    bot.polling()