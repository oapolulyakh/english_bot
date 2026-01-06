import telebot
from telebot import types
from random import shuffle


def get_main_menu():
    """
    Создает и возвращает клавиатуру с основными кнопками главного меню бота.

    Создает клавиатуру с четырьмя основными функциями бота:
    - ➕ Добавить слово: для добавления новых слов в словарь
    - 🎮 Тренировка: для запуска режима тренировки
    - 🗑 Удалить слово: для удаления слов из словаря
    - 📚 Сборники слов: для просмотра и добавления предустановленных сборников слов

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
    """
    Создает клавиатуру с перемешанными вариантами переводов для режима тренировки.

    Принимает список вариантов переводов, перемешивает их случайным образом
    и создает клавиатуру с этими вариантами. Используется в режиме тренировки
    для создания вопросов с несколькими вариантами ответов.

    :param words_list: Список вариантов переводов
    :type words_list: list[str]
    :return: Клавиатура с перемешанными вариантами ответов
    :rtype: telebot.types.ReplyKeyboardMarkup
    """
    buttons_word = words_list
    shuffle(buttons_word)
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(*buttons_word)
    return markup

def next_round_keyboard():
    """
    Создает клавиатуру для выбора действия после ответа в режиме тренировки.

    Создает одноразовую клавиатуру с двумя кнопками:
    - 'Дальше ➡️': для продолжения тренировки
    - '❌ Стоп': для завершения тренировки и возврата в главное меню

    :return: Клавиатура с вариантами продолжения тренировки
    :rtype: telebot.types.ReplyKeyboardMarkup
    """
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('Дальше ➡️'), types.KeyboardButton('❌ Стоп'))
    return markup

def preset_menu_keyboard():
    """
    Создает клавиатуру для действий с выбранным сборником слов.

    Создает клавиатуру с двумя кнопками для работы со сборниками слов:
    - 'Добавить ✅': для добавления всех слов из сборника в пользовательский словарь
    - '🔙 Назад': для возврата к выбору категорий сборников

    :return: Клавиатура с действиями для сборника слов
    :rtype: telebot.types.ReplyKeyboardMarkup
    """
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton('Добавить ✅'), types.KeyboardButton('🔙 Назад')]
    markup.add(*buttons)
    return markup

def list_category_keyboard(list_category):
    """
    Создает клавиатуру для выбора категории сборника слов.

    Принимает список категорий и создает клавиатуру с кнопками для каждой категории,
    а также добавляет кнопку '🔙 Назад' для возврата в главное меню. Клавиатура является
    одноразовой (исчезает после выбора).

    :param list_category: Список названий категорий сборников
    :type list_category: list[str]
    :return: Клавиатура с категориями сборников и кнопкой возврата
    :rtype: telebot.types.ReplyKeyboardMarkup
    """
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    buttons = [types.KeyboardButton(cat) for cat in list_category] + ['🔙 Назад']
    markup.add(*buttons)
    return markup