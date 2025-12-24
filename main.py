import telebot
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Word, PresetWord, create_tables
from preset_words import add_initial_presets
from telebot import types
from random import shuffle

load_dotenv()
token = os.getenv('token')
DSN = os.getenv('DSN')

engine = create_engine(DSN)
bot = telebot.TeleBot(token)
Session = sessionmaker(bind=engine)
create_tables(engine)
add_initial_presets(engine)


def random_word(cid):
    """
    Функция для создания списка слов при повторении
    """
    with Session() as s:
        user_id = s.query(User).filter(User.cid == cid).first()
        if not user_id:
            return []
        words = s.query(Word).filter(Word.user_id == user_id.id).all()
        words_list = [{'word': w.word, 'translation': w.translation} for w in words]

    shuffle(words_list)
    return words_list


def get_main_menu():
    """Основное меню"""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('➕ Добавить слово')
    btn2 = types.KeyboardButton('🎮 Тренировка')
    btn3 = types.KeyboardButton('🗑 Удалить слово')
    btn4 = types.KeyboardButton('📚 Сборники слов')
    markup.add(btn1, btn2, btn3, btn4)
    return markup


@bot.message_handler(commands=['start'])
def start(message):
    """Начало работы с ботом, если пользователь нет в базе, добавляет в БД"""
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
    bot.send_message(cid, "Выбери действие в меню 👇", reply_markup=get_main_menu())


@bot.message_handler(commands=['menu'])
def menu(message):
    cid = message.chat.id
    bot.send_message(cid, "Выбери действие в меню 👇", reply_markup=get_main_menu())


@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    """Обработчик тестового меню"""
    if message.text == '➕ Добавить слово':
        ask_word(message)
    elif message.text == '🎮 Тренировка':
        start_practise(message)
    elif message.text == '🗑 Удалить слово':
        delete_word(message)
    elif message.text == '📚 Сборники слов':
        show_collections(message)


@bot.message_handler(commands=['add'])
def ask_word(message):
    """Уточняет слово для добавления"""
    msg = bot.send_message(chat_id=message.chat.id, text="Введите слово на английском языке",
                           reply_markup=get_main_menu())
    bot.register_next_step_handler(msg, ask_translation)


def ask_translation(message):
    """Уточняет перевод для добавления"""
    cid = message.chat.id
    if message.content_type != 'text':
        msg = bot.send_message(cid, f"Это не текст. Введите слово буквами", reply_markup=get_main_menu())
        bot.register_next_step_handler(msg, ask_translation)
        return
    word = message.text.strip().lower()
    msg = bot.send_message(cid, f'Введите перевод для слова "{word}"', reply_markup=get_main_menu())
    bot.register_next_step_handler(msg, add_word_db, word)


def add_word_logic(session, word, translation, user_id):
    """Функция для добавления слова в БД"""
    existing_word = session.query(Word).filter(
        Word.word == word,
        Word.translation == translation,
        Word.user_id == user_id
    ).first()

    if existing_word:
        return False, f'Слово "{word}" уже есть.'
    else:
        obj = Word(word=word, translation=translation, user_id=user_id)
        session.add(obj)
        return True, f'Слово "{word}" добавлено.'


def add_word_db(message, word):
    """Добавление нового слова в БД пользователем"""
    cid = message.chat.id
    if message.content_type != 'text':
        msg = bot.send_message(cid, f"Это не текст, введите перевод буквами", reply_markup=get_main_menu())
        bot.register_next_step_handler(msg, add_word_db, word)
        return
    translation = message.text.strip().lower()

    try:
        with Session() as session:
            user = session.query(User).filter(User.cid == cid).first()
            if not user:
                bot.send_message(cid, "Введите /start", reply_markup=get_main_menu())
                return
            success, msg_text = add_word_logic(session, word, translation, user.id)
            session.commit()
            if success:
                bot.send_message(cid, f'Готово! {word} -> {translation} добавлено.', reply_markup=get_main_menu())
            else:
                bot.send_message(cid, f'Слово "{word}" ({translation}) уже есть в словаре.',
                                 reply_markup=get_main_menu())

    except Exception as e:
        print(e)
        bot.send_message(chat_id=cid, text="Ошибка записи.", reply_markup=get_main_menu())


@bot.message_handler(commands=['practise'])
def start_practise(message):
    """Функция тренировки, формирует список и кнопки для ответа"""
    cid = message.chat.id
    words_list = random_word(cid)
    if len(words_list) < 2:
        bot.send_message(chat_id=cid, text="Добавьте хотя бы 2 слова для практики", reply_markup=get_main_menu())
        return
    practice_word = words_list[0]['word']
    target_translation = words_list[0]['translation']
    buttons_word = [word['translation'] for word in words_list[0:4]]
    shuffle(buttons_word)
    print(f'{buttons_word=} создан список')
    ask_question(cid, practice_word, target_translation, buttons_word)


def ask_question(cid, practice_word, target_translation, buttons_word):
    """Задает вопрос и получает ответ"""
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    buttons = [types.KeyboardButton(word) for word in buttons_word]
    markup.add(*buttons)
    msg = bot.send_message(chat_id=cid, text=f'Как переводится "{practice_word}"?', reply_markup=markup)
    bot.register_next_step_handler(msg, check_answer, practice_word, target_translation, buttons_word)


def check_answer(message, practice_word, target_translation, buttons_word):
    """Проверяет правильность ответа, если ответ неправильный, убирает выбранную кнопку и повторяет вопрос"""
    cid = message.chat.id
    answer = message.text
    if answer != target_translation:
        if len(buttons_word) <= 2:
            bot.send_message(chat_id=cid,
                             text=f'Было близко! Правильный ответ: \n{practice_word} -> {target_translation}',
                             reply_markup=types.ReplyKeyboardRemove())
            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
            markup.add(types.KeyboardButton('Дальше ➡️'), types.KeyboardButton('❌ Стоп'))
            msg = bot.send_message(cid, "Продолжим?", reply_markup=markup)
            bot.register_next_step_handler(msg, next_round)
        else:
            buttons_word.remove(answer)
            bot.send_message(chat_id=cid, text=f'Неверно, попробуй еще раз',
                             reply_markup=types.ReplyKeyboardRemove())
            ask_question(cid, practice_word, target_translation, buttons_word)
    else:
        bot.send_message(chat_id=cid, text=f'Верно! ✅\n{practice_word} -> {target_translation}',
                         reply_markup=types.ReplyKeyboardRemove())
        buttons_word.clear()
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton('Дальше ➡️'), types.KeyboardButton('❌ Стоп'))
        msg = bot.send_message(cid, "Продолжим?", reply_markup=markup)
        bot.register_next_step_handler(msg, next_round)

    print(f'Список очищен')


def next_round(message):
    """Реализация кнопки следующего раунда и окончание тренировки"""
    if message.text == 'Дальше ➡️':
        start_practise(message)
    else:
        bot.send_message(message.chat.id, "Отличная тренировка!", reply_markup=get_main_menu())


@bot.message_handler(commands=['delete'])
def delete_word(message):
    """Запрос слова для удаления"""
    cid = message.chat.id
    msg = bot.send_message(chat_id=cid, text=f'Введи слово которое нужно удалить', reply_markup=get_main_menu())
    bot.register_next_step_handler(msg, delete_word_translate)


def delete_word_translate(message):
    """Выбор перевода для удаления"""
    cid = message.chat.id
    if message.content_type == 'text':
        del_word = message.text.strip().lower()
    else:
        bot.send_message(chat_id=cid, text='Кажется это не текст, для удаления слова введите текст',
                         reply_markup=get_main_menu())
        return
    with Session() as session:
        user = session.query(User).filter(User.cid == cid).first()
        translations = session.query(Word).filter(Word.word == del_word, Word.user_id == user.id).all()
        if translations:
            list_translations = [translation.translation for translation in translations]
            markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
            buttons = [types.KeyboardButton(translation) for translation in list_translations]
            markup.add(*buttons)
            trans = bot.send_message(chat_id=cid, text='Выбери перевод, который нужно удалить', reply_markup=markup)
            bot.register_next_step_handler(trans, delete_word_db, del_word)
        else:
            bot.send_message(chat_id=cid, text=f'В сборнике нет слова "{del_word}"', reply_markup=get_main_menu())


def delete_word_db(message, del_word):
    """Удаление слова с переводом из БД"""
    cid = message.chat.id
    trans = message.text
    with Session() as session:
        user = session.query(User).filter(User.cid == cid).first()
        word_obj = session.query(Word).filter(Word.word == del_word, Word.translation == trans,
                                              Word.user_id == user.id).first()
        if word_obj:
            session.delete(word_obj)
            session.commit()
            bot.send_message(chat_id=cid, text=f'Слово "{del_word}" - "{trans}" удалено', reply_markup=get_main_menu())
        else:
            bot.send_message(chat_id=cid, text=f'Не удалось найти слово для удаления.', reply_markup=get_main_menu())


def get_list_presets():
    """Получение актуального списка сборников слов"""
    with Session() as s:
        data = s.query(PresetWord.category).distinct(PresetWord.category).all()
        category = []
        for word in data:
            category += list(word)
        return category


def show_collections(message):
    """Отображение имеющихся сборников"""
    list_category = get_list_presets()
    cid = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    buttons = [types.KeyboardButton(cat) for cat in list_category] + ['🔙 Назад']
    markup.add(*buttons)
    msg = bot.send_message(cid, "Выберите тему:", reply_markup=markup)
    bot.register_next_step_handler(msg, show_words_presets)


def show_words_presets(message):
    """Отображение слов в коллекции для подтверждения обновления словаря"""
    cid = message.chat.id
    if message.text == '🔙 Назад':
        menu(message)
        return
    choice = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton('Добавить ✅'), types.KeyboardButton('🔙 Назад')]
    markup.add(*buttons)
    with Session() as session:
        preset_words = session.query(PresetWord).filter(PresetWord.category == choice).all()

        if not preset_words:
            bot.send_message(cid, "В этой категории пока нет слов.", reply_markup=get_main_menu())
            return

        text = f"📖 Слова в категории {choice}:\n\n"
        for pw in preset_words:
            text += f"▫️ {pw.word.title()} - {pw.translation}\n"

        msg = bot.send_message(chat_id=cid, text=text, reply_markup=markup)
        bot.register_next_step_handler(msg, add_preset_db, choice)


def add_preset_db(message, choice):
    """Добавление слов в словарь пользователя"""
    cid = message.chat.id
    answer = message.text
    if answer == "🔙 Назад":
        show_collections(message)
        return
    if answer != 'Добавить ✅':
        bot.send_message(cid, "Действие отменено.", reply_markup=get_main_menu())
        return
    with Session() as session:
        user = session.query(User).filter(User.cid == cid).first()
        if not user:
            bot.send_message(cid, "Ошибка авторизации.", reply_markup=get_main_menu())
            return
        preset_words = session.query(PresetWord).filter(PresetWord.category == choice).all()
        added_count = 0
        try:
            for pw in preset_words:
                success, _ = add_word_logic(session, pw.word, pw.translation, user.id)
                if success:
                    added_count += 1
            session.commit()
            bot.send_message(cid, f'✅ Успешно добавлено слов: {added_count}', reply_markup=get_main_menu())
        except Exception as e:
            print(e)
            session.rollback()
            bot.send_message(cid, 'Возникла ошибка при добавлении.', reply_markup=get_main_menu())


if "__main__" == __name__:
    print("Bot working...")
    bot.polling()
