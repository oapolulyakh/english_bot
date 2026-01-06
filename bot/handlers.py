import telebot

from bot.utils_bot import check_answer_logic, check_text
from telebot import types
from bot.keyboard import get_main_menu, random_words_keyboard, next_round_keyboard, preset_menu_keyboard, \
    list_category_keyboard
from core.config import bot
from db.utils_db import random_word, get_user, add_word_logic, get_words_logic, get_info_word, delete_word_translation, \
    get_list_presets, get_preset_words


@bot.message_handler(commands=['start'])
def start(message):
    """
    Обработчик команды /start. Инициализирует пользователя в системе.

    Если пользователь уже существует в базе данных, отправляет приветственное сообщение.
    Если пользователь новый, создает запись в базе данных и отправляет сообщение о знакомстве.
    После этого отображает главное меню.

    :param message: Объект сообщения от Telegram Bot API
    :type message: telebot.types.Message
    """
    cid = message.chat.id
    username = message.from_user.username
    user = get_user(cid)
    if user:
        bot.send_message(chat_id=cid, text=f"Привет! Приятно тебя снова видеть здесь)")
    else:
        try:
            add_word_logic(cid, username)
        except Exception as e:
            print(e)
    bot.send_message(cid, "Выбери действие в меню 👇", reply_markup=get_main_menu())


@bot.message_handler(commands=['menu'])
def menu(message):
    """
    Обработчик команды /menu. Восстанавливает отображение главного меню.

    Используется, если меню было скрыто или недоступно по какой-либо причине.

    :param message: Объект сообщения от Telegram Bot API
    :type message: telebot.types.Message
    """
    cid = message.chat.id
    bot.send_message(cid, "Выбери действие в меню 👇", reply_markup=get_main_menu())


@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    """
    Универсальный обработчик текстовых сообщений. Маршрутизирует команды в зависимости от выбранной кнопки меню.

    Обрабатывает следующие действия:
    - '➕ Добавить слово' - запускает процесс добавления нового слова
    - '🎮 Тренировка' - запускает режим тренировки
    - '🗑 Удалить слово' - запускает процесс удаления слова
    - '📚 Сборники слов' - отображает доступные сборники слов

    Если сообщение не соответствует ни одной команде, отправляет сообщение о необходимости начать заново.

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

    После получения сообщения регистрирует следующий шаг обработки - функцию ask_translation.

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
    запрашивает повторный ввод слова. После получения слова регистрирует следующий
    шаг - функцию add_word_db для добавления слова в базу данных.

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

    Проверяет, что сообщение содержит текст. Если нет - запрашивает повторный ввод.
    Получает пользователя из базы данных, вызывает add_word_logic для добавления слова,
    коммитит изменения и отправляет пользователю сообщение о результате операции.

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
        user = get_user(cid)
        user_id = user.id
        if not user:
            bot.send_message(cid, "Введите /start", reply_markup=get_main_menu())
            return
        success, _ = add_word_logic(word, translation, user_id)
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
    """
    Обработчик команды /practise. Запускает режим тренировки по словам.

    Получает список слов пользователя, перемешанный случайным образом. Если слов меньше двух,
    отправляет сообщение о необходимости добавить больше слов. Иначе выбирает первое слово
    из списка, формирует 4 варианта ответа (включая правильный) и вызывает ask_question.

    :param message: Объект сообщения от Telegram Bot API
    :type message: telebot.types.Message
    """
    cid = message.chat.id
    words_list = random_word(cid)
    practice_word = words_list[0]['word']
    target_translation = words_list[0]['translation']
    if len(words_list) < 2:
        bot.send_message(chat_id=cid, text="Добавьте хотя бы 2 слова для практики", reply_markup=get_main_menu())
        return
    buttons_word_list = [word["translation"] for word in words_list[0:4]]
    ask_question(cid, practice_word, target_translation, buttons_word_list)

def ask_question(cid, practice_word, target_translation, buttons_word_list):
    """
    Отправляет пользователю вопрос о переводе слова и создает клавиатуру с вариантами ответов.

    Создает клавиатуру с кнопками-вариантами ответов и отправляет вопрос пользователю.
    Регистрирует следующий шаг обработки - функцию check_answer для проверки ответа.

    :param markup:
    :param cid: ID чата пользователя в Telegram
    :type cid: int
    :param practice_word: Слово на английском языке, перевод которого нужно угадать
    :type practice_word: str
    :param target_translation: Правильный перевод слова
    :type target_translation: str
    :param buttons_word: Список вариантов переводов для кнопок (включая правильный)
    :type buttons_word: list[str]
    """

    msg = bot.send_message(chat_id=cid, text=f'Как переводится "{practice_word}"?',
                           reply_markup=random_words_keyboard(buttons_word_list))
    bot.register_next_step_handler(msg, check_answer, practice_word, target_translation, buttons_word_list)


def check_answer(message, practice_word, target_translation, buttons_word_list):
    """
    Проверяет правильность ответа пользователя на вопрос о переводе слова.

    Если ответ правильный:
    - Отправляет сообщение о правильном ответе
    - Предлагает продолжить тренировку или остановиться

    Если ответ неправильный:
    - Если вариантов ответа осталось 2 или меньше, показывает правильный ответ и предлагает продолжить
    - Иначе удаляет неправильный вариант из списка и повторяет вопрос с оставшимися вариантами

    :param message: Объект сообщения от Telegram Bot API с ответом пользователя
    :type message: telebot.types.Message
    :param practice_word: Слово на английском языке, перевод которого угадывается
    :type practice_word: str
    :param target_translation: Правильный перевод слова
    :type target_translation: str
    :param buttons_word: Список вариантов переводов (может изменяться при неправильных ответах)
    :type buttons_word: list[str]
    """
    cid = message.chat.id
    answer = message.text
    result, text = check_answer_logic(answer, target_translation, buttons_word_list, practice_word)
    if result == 3:
        bot.send_message(chat_id=cid,
                         text=text,
                         reply_markup = types.ReplyKeyboardRemove())
        msg = bot.send_message(cid, "Продолжим?", reply_markup=next_round_keyboard())
        bot.register_next_step_handler(msg, next_round)
    elif result == 2:
        bot.send_message(chat_id=cid, text=text,
                         reply_markup=types.ReplyKeyboardRemove())
        ask_question(cid, practice_word, target_translation, buttons_word_list)
    else:
        buttons_word_list.clear()
        bot.send_message(chat_id=cid, text=text,
                         reply_markup=types.ReplyKeyboardRemove())
        msg = bot.send_message(cid, "Продолжим?", reply_markup=next_round_keyboard())
        bot.register_next_step_handler(msg, next_round)

def next_round(message):
    """
    Обрабатывает выбор пользователя после завершения вопроса в режиме тренировки.

    Если пользователь выбрал "Дальше ➡️", запускает следующий раунд тренировки.
    Если пользователь выбрал "❌ Стоп", завершает тренировку и возвращает главное меню.

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

    После получения сообщения регистрирует следующий шаг обработки - функцию delete_word_translate.

    :param message: Объект сообщения от Telegram Bot API
    :type message: telebot.types.Message
    """
    cid = message.chat.id
    msg = bot.send_message(chat_id=cid, text=f'Введи слово которое нужно удалить', reply_markup=get_main_menu())
    bot.register_next_step_handler(msg, delete_word_translate)


def delete_word_translate(message):
    """
    Обрабатывает введенное пользователем слово и предлагает выбрать конкретный перевод для удаления.

    Проверяет, что сообщение содержит текст. Если слово найдено в словаре пользователя,
    создает клавиатуру со всеми переводами этого слова и предлагает выбрать, какой именно
    перевод нужно удалить. Если слово не найдено, сообщает об этом пользователю.

    :param message: Объект сообщения от Telegram Bot API с введенным словом для удаления
    :type message: telebot.types.Message
    """
    cid = message.chat.id
    is_text, del_word = check_text(message)
    if not is_text:
        bot.send_message(chat_id=cid, text='Кажется это не текст, для удаления слова введите текст',
                         reply_markup=get_main_menu())
        return
    user = get_user(cid)
    translations = get_words_logic(del_word, user.id)
    if translations:
        list_translations = [translation.translation for translation in translations]
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
    user = get_user(cid)
    word_obj = get_info_word(del_word, trans, user.id)
    if word_obj:
        delete_word_translation(word_obj)
        bot.send_message(chat_id=cid, text=f'Слово "{del_word}" - "{trans}" удалено', reply_markup=get_main_menu())
    else:
        bot.send_message(chat_id=cid, text=f'Не удалось найти слово для удаления.', reply_markup=get_main_menu())


@bot.message_handler(commands=['collections'])
def show_collections(message):
    """
    Отображает список доступных сборников (категорий) предустановленных слов.

    Получает список всех категорий из базы данных и создает клавиатуру с кнопками
    для выбора категории. Также добавляет кнопку "🔙 Назад" для возврата в главное меню.
    После выбора категории регистрирует следующий шаг - функцию show_words_presets.

    :param message: Объект сообщения от Telegram Bot API
    :type message: telebot.types.Message
    """
    list_category = get_list_presets()
    cid = message.chat.id
    msg = bot.send_message(cid, "Выберите тему:", reply_markup=list_category_keyboard(list_category))
    bot.register_next_step_handler(msg, show_words_presets)


def show_words_presets(message):
    """
    Отображает все слова из выбранной категории сборника и предлагает добавить их в словарь.

    Если пользователь выбрал "🔙 Назад", возвращает в меню выбора сборников.
    Иначе получает все слова из выбранной категории, форматирует их в читаемый список
    и отправляет пользователю с предложением добавить слова в свой словарь.
    Регистрирует следующий шаг - функцию add_preset_db.

    :param message: Объект сообщения от Telegram Bot API с выбранной категорией
    :type message: telebot.types.Message
    """
    cid = message.chat.id
    if message.text == '🔙 Назад':
        menu(message)
        return
    choice = message.text
    preset_words =  get_preset_words(choice)
    if not preset_words:
        bot.send_message(cid, "В этой категории пока нет слов.", reply_markup=get_main_menu())
        return

    text = f"📖 Слова в категории {choice}:\n\n"
    for pw in preset_words:
        text += f"▫️ {pw.word.title()} - {pw.translation}\n"

    msg = bot.send_message(chat_id=cid, text=text, reply_markup=preset_menu_keyboard())
    bot.register_next_step_handler(msg, add_preset_db, preset_words)


def add_preset_db(message, preset_words):
    """
    Добавляет все слова из выбранного сборника в словарь пользователя.

    Если пользователь выбрал "🔙 Назад", возвращает к списку сборников.
    Если пользователь выбрал "Добавить ✅", получает все слова из выбранной категории
    и добавляет их в словарь пользователя через функцию add_word_logic.
    Подсчитывает количество успешно добавленных слов и отправляет результат пользователю.
    Если слово уже существует в словаре пользователя, оно пропускается.

    :param preset_words:
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
    user = get_user(cid)
    if not user:
        bot.send_message(cid, "Ошибка авторизации.", reply_markup=get_main_menu())
        return
    added_count = 0
    try:
        for pw in preset_words:
            success, _ = add_word_logic(pw.word, pw.translation, user.id)
            if success:
                added_count += 1
        bot.send_message(cid, f'✅ Успешно добавлено слов: {added_count}', reply_markup=get_main_menu())
    except Exception as e:
        print(e)
        bot.send_message(cid, 'Возникла ошибка при добавлении.', reply_markup=get_main_menu())

