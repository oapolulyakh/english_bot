import telebot
from telebot import types
from random import shuffle


def get_main_menu():
    """
    Создает и возвращает клавиатуру с основными кнопками главного меню бота.

    Кнопки меню:
    - ➕ Добавить слово
    - 🎮 Тренировка
    - 🗑 Удалить слово
    - 📚 Сборники слов

    :return: Объект клавиатуры с основными кнопками меню
    :rtype: telebot.types.ReplyKeyboardMarkup
    """
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('➕ Добавить слово')
    btn2 = types.KeyboardButton('🎮 Тренировка')
    btn3 = types.KeyboardButton('🗑 Удалить слово')
    btn4 = types.KeyboardButton('📚 Сборники слов')
    markup.add(btn1, btn2, btn3, btn4)
    return markup

def random_words_keyboard(words_list):
    buttons_word = words_list
    shuffle(buttons_word)
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(*buttons_word)
    return markup

def next_round_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('Дальше ➡️'), types.KeyboardButton('❌ Стоп'))
    return markup

def preset_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton('Добавить ✅'), types.KeyboardButton('🔙 Назад')]
    markup.add(*buttons)
    return markup

def list_category_keyboard(list_category):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    buttons = [types.KeyboardButton(cat) for cat in list_category] + ['🔙 Назад']
    markup.add(*buttons)
    return markup