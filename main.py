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
    Получает список слов пользователя из базы данных и перемешивает их для режима тренировок.
    
    :param cid: ID чата пользователя в Telegram
    :type cid: int
    :return: Список словарей с ключами 'word' и 'translation', перемешанный случайным образом
    :rtype: list[dict]
    :return: Пустой список, если пользователь не найден в базе данных
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


def add_word_logic(session, word, translation, user_id):
    """
    Логика добавления слова в базу данных. Проверяет наличие дубликатов перед добавлением.
    
    Проверяет, существует ли уже слово с таким же текстом и переводом для данного пользователя.
    Если слово уже существует, возвращает False и сообщение об ошибке.
    Если слова нет, создает новый объект Word и добавляет его в сессию.
    
    :param session: Сессия SQLAlchemy для работы с базой данных
    :type session: sqlalchemy.orm.Session
    :param word: Слово на английском языке (в нижнем регистре)
    :type word: str
    :param translation: Перевод слова (в нижнем регистре)
    :type translation: str
    :param user_id: ID пользователя в базе данных
    :type user_id: int
    :return: Кортеж (успех_добавления, сообщение)
    :rtype: tuple[bool, str]
    """
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
        return True


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
    if len(words_list) < 2:
        bot.send_message(chat_id=cid, text="Добавьте хотя бы 2 слова для практики", reply_markup=get_main_menu())
        return
    practice_word = words_list[0]['word']
    target_translation = words_list[0]['translation']
    buttons_word = [word['translation'] for word in words_list[0:4]]
    shuffle(buttons_word)
    ask_question(cid, practice_word, target_translation, buttons_word)


def ask_question(cid, practice_word, target_translation, buttons_word):
    """
    Отправляет пользователю вопрос о переводе слова и создает клавиатуру с вариантами ответов.
    
    Создает клавиатуру с кнопками-вариантами ответов и отправляет вопрос пользователю.
    Регистрирует следующий шаг обработки - функцию check_answer для проверки ответа.
    
    :param cid: ID чата пользователя в Telegram
    :type cid: int
    :param practice_word: Слово на английском языке, перевод которого нужно угадать
    :type practice_word: str
    :param target_translation: Правильный перевод слова
    :type target_translation: str
    :param buttons_word: Список вариантов переводов для кнопок (включая правильный)
    :type buttons_word: list[str]
    """
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    buttons = [types.KeyboardButton(word) for word in buttons_word]
    markup.add(*buttons)
    msg = bot.send_message(chat_id=cid, text=f'Как переводится "{practice_word}"?', reply_markup=markup)
    bot.register_next_step_handler(msg, check_answer, practice_word, target_translation, buttons_word)


def check_answer(message, practice_word, target_translation, buttons_word):
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
            if answer in buttons_word:
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
    """
    Получает список всех уникальных категорий (сборников) предустановленных слов из базы данных.
    
    :return: Список названий категорий сборников слов
    :rtype: list[str]
    """
    with Session() as s:
        data = s.query(PresetWord.category).distinct(PresetWord.category).all()
        category = []
        for word in data:
            category += list(word)
        return category


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
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    buttons = [types.KeyboardButton(cat) for cat in list_category] + ['🔙 Назад']
    markup.add(*buttons)
    msg = bot.send_message(cid, "Выберите тему:", reply_markup=markup)
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
    """
    Добавляет все слова из выбранного сборника в словарь пользователя.
    
    Если пользователь выбрал "🔙 Назад", возвращает к списку сборников.
    Если пользователь выбрал "Добавить ✅", получает все слова из выбранной категории
    и добавляет их в словарь пользователя через функцию add_word_logic.
    Подсчитывает количество успешно добавленных слов и отправляет результат пользователю.
    Если слово уже существует в словаре пользователя, оно пропускается.
    
    :param message: Объект сообщения от Telegram Bot API с выбором пользователя
    :type message: telebot.types.Message
    :param choice: Название выбранной категории сборника
    :type choice: str
    """
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
    bot.polling(non_stop=True, skip_pending=True)
