import telebot
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()
token = os.getenv('token')
DSN = os.getenv('DSN')

engine = create_engine(DSN)
bot = telebot.TeleBot(token)
Session = sessionmaker(bind=engine)

