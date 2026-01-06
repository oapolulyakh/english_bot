import logging

from sqlalchemy.exc import IntegrityError

from db.models import User, Word, PresetWord
from random import shuffle
from core.config import Session


def get_random_words_list(cid):
    """
    Получает и перемешивает список слов пользователя для режима тренировок.

    Получает все слова пользователя из базы данных, преобразует их в формат словарей
    и перемешивает случайным образом. Используется для создания случайных вопросов
    в режиме тренировки. Возвращает пустой список, если пользователь не найден
    или у него нет слов в словаре.

    :param cid: ID чата пользователя в Telegram
    :type cid: int
    :return: Список словарей с ключами 'word' и 'translation', перемешанный случайным образом
    :rtype: list[dict]
    """
    with Session() as s:
        words = s.query(Word).join(User).filter(User.cid == cid).all()
        if not words:
            return []
        words_list = [w.to_dict() for w in words]

    shuffle(words_list)
    return words_list

def exist_word_translation(word, translation, user_id):
    with Session() as session:
        existing_word = session.query(Word).filter(
            Word.word == word,
            Word.translation == translation,
            Word.user_id == user_id
        ).first()
        return bool(existing_word)

def add_word_to_db(word, translation, user_id):
    """
    Добавляет новое слово с переводом в базу данных пользователя.

    Проверяет наличие дубликата перед добавлением. Если слово с таким переводом
    уже существует у пользователя, не добавляет его повторно. При успешном добавлении
    возвращает True, при ошибке или существовании дубликата - False.

    :param word: Слово на английском языке
    :type word: str
    :param translation: Перевод слова
    :type translation: str
    :param user_id: ID пользователя в базе данных
    :type user_id: int
    :return: True при успешном добавлении, False при ошибке или дубликате
    :rtype: bool
    """
    if exist_word_translation(word, translation, user_id):
        return False
    obj = Word(word=word, translation=translation, user_id=user_id)
    with Session() as session:
        try:
            session.add(obj)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logging.exception(e)
            return False


def get_id_user(cid):
    """
    Получает ID пользователя по его chat ID в Telegram.

    Выполняет поиск пользователя в базе данных по его chat ID (cid).
    Используется для идентификации пользователя при выполнении операций
    с его словарем. Возвращает None, если пользователь не найден.

    :param cid: ID чата пользователя в Telegram
    :type cid: int
    :return: ID пользователя в базе данных или None если пользователь не найден
    :rtype: int or None
    """

    with Session() as session:
        user_id = session.query(User.id).filter(User.cid == cid).scalar()
        return user_id



def create_user(cid, username):
    """
    Создает нового пользователя в базе данных.

    Пытается создать запись о новом пользователе с указанным chat ID и именем.
    Если пользователь с таким chat ID уже существует, возвращает его ID.
    При успешном создании возвращает ID нового пользователя. В случае ошибки
    возвращает None.

    :param cid: ID чата пользователя в Telegram
    :type cid: int
    :param username: Имя пользователя в Telegram
    :type username: str
    :return: ID пользователя или None при ошибке
    :rtype: int or None
    """
    if get_id_user(cid):
        return get_id_user(cid)  # Уже существует

    with Session() as session:
        obj = User(cid=cid, username=username)
        try:
            session.add(obj)
            session.commit()
            user_id = obj.id
            return user_id
        except IntegrityError:
            session.rollback()
            logging.exception("Ошибка создания пользователя")
            return None

def get_word_translations(word, user_id):
    """
    Получает список всех переводов для конкретного слова пользователя.

    Выполняет поиск всех переводов указанного слова у конкретного пользователя.
    Используется при удалении слова, когда нужно выбрать конкретный перевод
    для удаления. Возвращает пустой список, если переводы не найдены.

    :param word: Слово на английском языке для поиска
    :type word: str
    :param user_id: ID пользователя в базе данных
    :type user_id: int
    :return: Список словарей с информацией о словах (может быть пустым)
    :rtype: list[dict]
    """
    with Session() as session:
        words = session.query(Word).filter(Word.word == word, Word.user_id == user_id).all()
        return [w.to_dict() for w in words]



def remove_user_word(word, translation, user_id):
    """
    Удаляет конкретное слово с переводом из словаря пользователя.

    Находит и удаляет слово по его тексту, переводу и ID пользователя.
    Используется при удалении конкретного перевода слова из словаря пользователя.
    Возвращает True при успешном удалении, False если слово не найдено.

    :param word: Слово на английском языке для удаления
    :type word: str
    :param translation: Перевод слова для удаления
    :type translation: str
    :param user_id: ID пользователя в базе данных
    :type user_id: int
    :return: True при успешном удалении, False если слово не найдено
    :rtype: bool
    """
    with Session() as session:
        word_obj = session.query(Word).filter(
            Word.word == word,
            Word.translation == translation,
            Word.user_id == user_id
        ).first()
        if not word_obj:
            return False
        session.delete(word_obj)
        session.commit()
        return True


def get_preset_categories():
    """
    Получает список всех уникальных категорий предустановленных слов из базы данных.

    Выполняет запрос к базе данных для получения всех уникальных значений
    категории из таблицы предустановленных слов. Используется для отображения
    доступных тем сборников слов пользователю.

    :return: Список названий категорий сборников слов
    :rtype: list[str]
    """
    with Session() as s:
        data = s.query(PresetWord.category).distinct(PresetWord.category).all()
        category = [row[0] for row in data]
        return category


def get_preset_words(category):
    """
    Получает все слова из указанной категории сборника.

    Выполняет запрос к базе данных для получения всех слов из таблицы
    предустановленных слов, фильтруя по указанной категории. Используется
    для отображения содержимого выбранного сборника слов пользователю.
    Возвращает пустой список, если слова не найдены.

    :param category: Название категории сборника слов
    :type category: str
    :return: Список словарей с информацией о словах из категории (может быть пустым)
    :rtype: list[dict]
    """
    with Session() as session:
        preset_words = session.query(PresetWord).filter(PresetWord.category == category).all()
        return [pw.to_dict() for pw in preset_words]