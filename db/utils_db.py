from db.models import User, Word, PresetWord
from random import shuffle
from core.config import Session


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


def add_word_logic(word, translation, user_id):
    """
    Логика добавления слова в базу данных. Проверяет наличие дубликатов перед добавлением.

    Проверяет, существует ли уже слово с таким же текстом и переводом для данного пользователя.
    Если слово уже существует, возвращает False и сообщение об ошибке.
    Если слова нет, создает новый объект Word и добавляет его в сессию.

    :param word: Слово на английском языке (в нижнем регистре)
    :type word: str
    :param translation: Перевод слова (в нижнем регистре)
    :type translation: str
    :param user_id: ID пользователя в базе данных
    :type user_id: int
    :return: Кортеж (успех_добавления, сообщение)
    :rtype: tuple[bool, str]
    """
    with Session() as session:
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
            session.commit()
            return True, None

def get_user(cid):
    with Session() as session:
        user = session.query(User).filter(User.cid == cid).first()
        if not user:
            return False
        return user

def add_user_logic(cid, username):
    with Session() as session:
        obj = User(cid=cid, username=username)
        session.add(obj)
        session.commit()

def get_words_logic(word, user_id):
    with Session() as session:
        words = session.query(Word).filter(Word.word == word, Word.user_id == user_id).all()
        return words

def get_info_word(word, translation, user_id):
    with Session() as session:
        word_obj = session.query(Word).filter(Word.word == word, Word.translation == translation,
                                          Word.user_id == user_id).first()
        return word_obj

def delete_word_translation(word_obj):
    try:
        with Session() as session:
            session.delete(word_obj)
            session.commit()
    except Exception as e:
        print(e)


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


def get_preset_words(category):
    with Session() as session:
        preset_words = session.query(PresetWord).filter(PresetWord.category == category).all()
        return preset_words
