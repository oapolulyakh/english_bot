import logging
import telebot
from enum import IntEnum

class AnswerResult(IntEnum):
    CORRECT = 1
    INCORRECT_RETRY = 2
    INCORRECT_FINAL = 3


from bot.utils_bot import check_answer_logic, check_text
from telebot import types
from bot.keyboard import get_main_menu, random_words_keyboard, next_round_keyboard, preset_menu_keyboard, \
    list_category_keyboard
from core.config import bot
from db.utils_db import get_random_words_list, get_id_user, add_word_to_db, remove_user_word, \
    get_preset_words, create_user, get_word_translations, get_preset_categories


@bot.message_handler(commands=['start'])
def start(message):
    """
    Обработчик команды /start. Инициализирует пользователя в системе.

    Проверяет существование пользователя в базе данных. Если пользователь найден, отправляет
    приветственное сообщение. Если пользователь новый, создает запись в базе данных и
    отправляет сообщение о знакомстве. В любом случае отображает главное меню.

    :param message: Объект сообщения от Telegram Bot API
    :type message: telebot.types.Message
    """
    cid = message.chat.id
    username = message.from_user.username
    user_id = get_id_user(cid)
    if user_id:
        bot.send_message(chat_id=cid, text=f"Привет! Приятно тебя снова видеть здесь)")
    else:
        try:
            create_user(cid, username)
        except Exception as e:
            logging.exception(f"Возникла ошибка при создании пользователя")

    bot.send_message(cid, "Выбери действие в меню 👇", reply_markup=get_main_menu())


@bot.message_handler(commands=['menu'])
def menu(message):
    """
    Обработчик команды /menu. Восстанавливает отображение главного меню.

    Отправляет пользователю приветственное сообщение с предложением выбрать действие
    через клавиатуру главного меню. Используется для восстановления меню, если оно
    было скрыто или недоступно.

    :param message: Объект сообщения от Telegram Bot API
    :type message: telebot.types.Message
    """
    cid = message.chat.id
    bot.send_message(cid, "Выбери действие в меню 👇", reply_markup=get_main_menu())


@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    """
    Универсальный обработчик текстовых сообщений. Маршрутизирует команды в зависимости от выбранной кнопки меню.

    Обрабатывает нажатия на кнопки главного меню, запуская соответствующие функции:
    - '➕ Добавить слово': запускает процесс добавления нового слова
    - '🎮 Тренировка': запускает режим тренировки
    - '🗑 Удалить слово': запускает процесс удаления слова
    - '📚 Сборники слов': отображает доступные сборники слов

    Если сообщение не соответствует ни одной команде, отправляет сообщение о необходимости начать заново
    через главное меню.

    :param message: Объект сообщения от Telegram Bot API
    :type message: telebot.types.Message
    """
    if message.text == '➕ Добавить слово':
        ask_word(message)
    elif message.text == '🎮 Тренировка':
        start_practise(message)
    elif message.text == '🗑 Удалить слово':
        delete_word(message)
    elif message.text == '📚 Сборники слов':
        show_collections(message)
    else:
        bot.send_message(
            message.chat.id,
            "Я перезагрузился и забыл, о чем мы говорили. 🤖\nНачни сначала через меню.",
            reply_markup=get_main_menu()
        )


@bot.message_handler(commands=['add'])
def ask_word(message):
    """
    Обработчик команды /add. Запрашивает у пользователя слово на английском языке для добавления в словарь.

    Отправляет сообщение с запросом ввода слова и регистрирует следующий шаг обработки,
    который будет ожидать ввод перевода от пользователя.

    :param message: Объект сообщения от Telegram Bot API
    :type message: telebot.types.Message
    """
    msg = bot.send_message(chat_id=message.chat.id, text="Введите слово на английском языке",
                           reply_markup=get_main_menu())
    bot.register_next_step_handler(msg, ask_translation)


def ask_translation(message):
    """
    Запрашивает перевод для ранее введенного слова.

    Проверяет, что сообщение содержит текст. Если сообщение не является текстовым,
    отправляет сообщение об ошибке и повторно запрашивает ввод слова. Если ввод корректен,
    запрашивает перевод для введенного слова и регистрирует следующий шаг обработки,
    который будет добавлять слово в базу данных.

    :param message: Объект сообщения от Telegram Bot API с введенным словом
    :type message: telebot.types.Message
    """
    cid = message.chat.id
    if message.content_type != 'text':
        msg = bot.send_message(cid, f"Это не текст. Введите слово буквами", reply_markup=get_main_menu())
        bot.register_next_step_handler(msg, ask_translation)
        return
    word = message.text.strip().lower()
    msg = bot.send_message(cid, f'Введите перевод для слова "{word}"', reply_markup=get_main_menu())
    bot.register_next_step_handler(msg, add_word_db, word)


def add_word_db(message, word):
    """
    Добавляет новое слово с переводом в базу данных пользователя.

    Проверяет корректность ввода перевода. Если ввод некорректен, запрашивает повторный ввод.
    Если ввод корректен, получает пользователя из базы данных и пытается добавить слово с переводом.
    Отправляет пользователю соответствующее сообщение о результате операции.

    :param message: Объект сообщения от Telegram Bot API с переводом слова
    :type message: telebot.types.Message
    :param word: Слово на английском языке, для которого запрашивается перевод
    :type word: str
    """
    cid = message.chat.id
    is_translation, translation = check_text(message)
    if not is_translation:
        msg = bot.send_message(cid, f"Это не текст, введите перевод буквами", reply_markup=get_main_menu())
        bot.register_next_step_handler(msg, add_word_db, word)
        return

    try:
        user_id = get_id_user(cid)
        if not user_id:
            bot.send_message(cid, "Введите /start", reply_markup=get_main_menu())
            return
        success = add_word_to_db(word, translation, user_id)
        if success:
            bot.send_message(cid, f'Готово! {word} -> {translation} добавлено.', reply_markup=get_main_menu())
        else:
            bot.send_message(cid, f'Слово "{word}" ({translation}) уже есть в словаре.',
                             reply_markup=get_main_menu())
    except Exception as e:
        logging.exception(f"Возникла ошибка при добавлении слова")
        bot.send_message(chat_id=cid, text="Ошибка записи.", reply_markup=get_main_menu())


@bot.message_handler(commands=['practise'])
def start_practise(message):
    """
    Обработчик команды /practise. Запускает режим тренировки по словам.

    Получает случайный список слов пользователя. Если слов меньше двух, отправляет
    сообщение о необходимости добавить больше слов. Иначе выбирает первое слово
    из списка и формирует 4 варианта ответа (включая правильный), затем запрашивает
    ответ у пользователя.

    :param message: Объект сообщения от Telegram Bot API
    :type message: telebot.types.Message
    """
    cid = message.chat.id
    words_list = get_random_words_list(cid)
    if len(words_list) < 2:
        bot.send_message(chat_id=cid, text="Добавьте хотя бы 2 слова для практики", reply_markup=get_main_menu())
        return
    practice_word = words_list[0]['word']
    target_translation = words_list[0]['translation']
    buttons_word_list = [word["translation"] for word in words_list[0:4]]
    ask_question(cid, practice_word, target_translation, buttons_word_list)


def ask_question(cid, practice_word, target_translation, buttons_word_list):
    """
    Отправляет пользователю вопрос о переводе слова и создает клавиатуру с вариантами ответов.

    Формирует вопрос о переводе заданного слова и создает клавиатуру с вариантами ответов.
    Отправляет вопрос пользователю и регистрирует следующий шаг обработки, который будет
    ожидать ответ пользователя и проверять его.

    :param cid: ID чата пользователя в Telegram
    :type cid: int
    :param practice_word: Слово на английском языке, перевод которого нужно угадать
    :type practice_word: str
    :param target_translation: Правильный перевод слова
    :type target_translation: str
    :param buttons_word_list: Список вариантов переводов для кнопок (включая правильный)
    :type buttons_word_list: list[str]
    """

    msg = bot.send_message(chat_id=cid, text=f'Как переводится "{practice_word}"?',
                           reply_markup=random_words_keyboard(buttons_word_list))
    bot.register_next_step_handler(msg, check_answer, practice_word, target_translation, buttons_word_list)


def check_answer(message, practice_word, target_translation, buttons_word_list):
    """
    Проверяет правильность ответа пользователя на вопрос о переводе слова.

    Обрабатывает ответ пользователя и определяет, является ли он правильным. Если ответ
    правильный, отправляет подтверждение и предлагает продолжить или завершить тренировку.
    Если ответ неправильный, в зависимости от количества оставшихся вариантов либо предлагает
    попробовать снова с оставшимися вариантами, либо показывает правильный ответ и предлагает
    продолжить тренировку.

    :param message: Объект сообщения от Telegram Bot API с ответом пользователя
    :type message: telebot.types.Message
    :param practice_word: Слово на английском языке, перевод которого угадывается
    :type practice_word: str
    :param target_translation: Правильный перевод слова
    :type target_translation: str
    :param buttons_word_list: Список вариантов переводов (может изменяться при неправильных ответах)
    :type buttons_word_list: list[str]
    """
    cid = message.chat.id
    answer = message.text
    result, text = check_answer_logic(answer, target_translation, buttons_word_list, practice_word)
    if result == AnswerResult.INCORRECT_FINAL or result == AnswerResult.CORRECT:
        bot.send_message(chat_id=cid,
                         text=text,
                         reply_markup=types.ReplyKeyboardRemove())
        msg = bot.send_message(cid, "Продолжим?", reply_markup=next_round_keyboard())
        bot.register_next_step_handler(msg, next_round)
    elif result == AnswerResult.INCORRECT_RETRY:
        bot.send_message(chat_id=cid, text=text,
                         reply_markup=types.ReplyKeyboardRemove())
        ask_question(cid, practice_word, target_translation, buttons_word_list)


def next_round(message):
    """
    Обрабатывает выбор пользователя после завершения вопроса в режиме тренировки.

    Обрабатывает ответ пользователя на предложение продолжить тренировку. Если пользователь
    выбрал "Дальше ➡️", запускает следующий раунд тренировки. Если пользователь выбрал
    "❌ Стоп", завершает тренировку и возвращает пользователя в главное меню.

    :param message: Объект сообщения от Telegram Bot API с выбором пользователя
    :type message: telebot.types.Message
    """
    if message.text == 'Дальше ➡️':
        start_practise(message)
    else:
        bot.send_message(message.chat.id, "Отличная тренировка!", reply_markup=get_main_menu())


@bot.message_handler(commands=['delete'])
def delete_word(message):
    """
    Обработчик команды /delete. Запрашивает у пользователя слово для удаления из словаря.

    Отправляет сообщение с запросом ввода слова для удаления и регистрирует следующий шаг
    обработки, который будет обрабатывать введенное слово и предлагать выбор перевода для удаления.

    :param message: Объект сообщения от Telegram Bot API
    :type message: telebot.types.Message
    """
    cid = message.chat.id
    msg = bot.send_message(chat_id=cid, text=f'Введи слово которое нужно удалить', reply_markup=get_main_menu())
    bot.register_next_step_handler(msg, delete_word_translate)


def delete_word_translate(message):
    """
    Обрабатывает введенное пользователем слово и предлагает выбрать конкретный перевод для удаления.

    Проверяет корректность ввода. Если ввод корректен, проверяет наличие слова в словаре пользователя.
    Если слово найдено, создает клавиатуру со всеми его переводами и предлагает пользователю
    выбрать, какой именно перевод нужно удалить. Если слово не найдено, сообщает об этом пользователю.

    :param message: Объект сообщения от Telegram Bot API с введенным словом для удаления
    :type message: telebot.types.Message
    """
    cid = message.chat.id
    is_text, del_word = check_text(message)
    if not is_text:
        bot.send_message(chat_id=cid, text='Кажется это не текст, для удаления слова введите текст',
                         reply_markup=get_main_menu())
        return
    user_id = get_id_user(cid)
    translations = get_word_translations(del_word, user_id)
    if translations:
        list_translations = [translation['translation'] for translation in translations]
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
        buttons = [types.KeyboardButton(translation) for translation in list_translations]
        markup.add(*buttons)
        trans = bot.send_message(chat_id=cid, text='Выбери перевод, который нужно удалить', reply_markup=markup)
        bot.register_next_step_handler(trans, delete_word_db, del_word)
    else:
        bot.send_message(chat_id=cid, text=f'В сборнике нет слова "{del_word}"', reply_markup=get_main_menu())


def delete_word_db(message, del_word):
    """
    Удаляет слово с указанным переводом из базы данных пользователя.

    Находит слово в базе данных по тексту слова, переводу и ID пользователя.
    Если слово найдено, удаляет его и отправляет подтверждение пользователю.
    Если слово не найдено, отправляет сообщение об ошибке.

    :param message: Объект сообщения от Telegram Bot API с выбранным переводом для удаления
    :type message: telebot.types.Message
    :param del_word: Слово на английском языке, которое нужно удалить
    :type del_word: str
    """
    cid = message.chat.id
    trans = message.text
    user_id = get_id_user(cid)
    success = remove_user_word(del_word, trans, user_id)
    if success:
        bot.send_message(chat_id=cid, text=f'Слово "{del_word}" - "{trans}" удалено', reply_markup=get_main_menu())
    else:
        bot.send_message(chat_id=cid, text=f'Не удалось найти слово для удаления.', reply_markup=get_main_menu())


@bot.message_handler(commands=['collections'])
def show_collections(message):
    """
    Отображает список доступных сборников (категорий) предустановленных слов.

    Получает список всех категорий из базы данных и создает клавиатуру с кнопками
    для выбора категории. Также добавляет кнопку "🔙 Назад" для возврата в главное меню.
    Отправляет пользователю сообщение с предложением выбрать тему и регистрирует
    следующий шаг обработки, который будет отображать слова выбранной категории.

    :param message: Объект сообщения от Telegram Bot API
    :type message: telebot.types.Message
    """
    list_category = get_preset_categories()
    cid = message.chat.id
    msg = bot.send_message(cid, "Выберите тему:", reply_markup=list_category_keyboard(list_category))
    bot.register_next_step_handler(msg, show_words_presets)


def show_words_presets(message):
    """
    Отображает все слова из выбранной категории сборника и предлагает добавить их в словарь.

    Обрабатывает выбор пользователя. Если пользователь выбрал "🔙 Назад",
    возвращает в меню выбора сборников. Иначе получает все слова из выбранной категории,
    форматирует их в читаемый список и отправляет пользователю с предложением добавить
    слова в свой словарь. Регистрирует следующий шаг обработки, который будет добавлять
    выбранные слова в словарь пользователя.

    :param message: Объект сообщения от Telegram Bot API с выбранной категорией
    :type message: telebot.types.Message
    """
    cid = message.chat.id
    if message.text == '🔙 Назад':
        menu(message)
        return
    choice = message.text
    preset_words = get_preset_words(choice)
    if not preset_words:
        bot.send_message(cid, "В этой категории пока нет слов.", reply_markup=get_main_menu())
        return

    text = f"📖 Слова в категории {choice}:\n\n"
    for pw in preset_words:
        text += f"▫️ {pw['word'].title()} - {pw['translation']}\n"

    msg = bot.send_message(chat_id=cid, text=text, reply_markup=preset_menu_keyboard())
    bot.register_next_step_handler(msg, add_preset_db, preset_words)


def add_preset_db(message, preset_words):
    """
    Добавляет все слова из выбранного сборника в словарь пользователя.

    Обрабатывает выбор пользователя. Если пользователь выбрал "🔙 Назад",
    возвращает к списку сборников. Если пользователь выбрал "Добавить ✅",
    добавляет все слова из выбранной категории в словарь пользователя.
    Подсчитывает количество успешно добавленных слов и отправляет результат пользователю.
    Пропускает слова, которые уже существуют в словаре пользователя.

    :param preset_words: Список слов из выбранного сборника
    :type preset_words: list
    :param message: Объект сообщения от Telegram Bot API с выбором пользователя
    :type message: telebot.types.Message
    """
    cid = message.chat.id
    answer = message.text
    if answer == "🔙 Назад":
        show_collections(message)
        return
    if answer != 'Добавить ✅':
        bot.send_message(cid, "Действие отменено.", reply_markup=get_main_menu())
        return
    user_id = get_id_user(cid)
    if not user_id:
        bot.send_message(cid, "Ошибка авторизации.", reply_markup=get_main_menu())
        return
    added_count = 0
    try:
        for pw in preset_words:
            success = add_word_to_db(pw['word'], pw['translation'], user_id)
            if success:
                added_count += 1
        bot.send_message(cid, f'✅ Успешно добавлено слов: {added_count}', reply_markup=get_main_menu())
    except Exception as e:
        logging.exception(f"Возникла ошибка при добавлении сборника пользователю")
        bot.send_message(cid, 'Возникла ошибка при добавлении.', reply_markup=get_main_menu())
