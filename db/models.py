
from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    cid = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=True)

    words = relationship("Word", back_populates="user", cascade="all, delete-orphan")

    def __str__(self):
        return f"User {self.cid}: {self.username}"

    def to_dict(self):
        """
        Преобразует объект пользователя в словарь.

        Используется для сериализации объекта пользователя в формат словаря,
        который может быть легко передан или сохранен. Включает основную информацию
        о пользователе: ID, имя пользователя и chat ID.

        :return: Словарь с данными пользователя
        :rtype: dict[str, any]
        """
        return {
            "id": self.id,
            "username": self.username,
            "cid": self.cid
        }


class Word(Base):
    __tablename__ = 'words'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    word = Column(String, nullable=False)
    translation = Column(String, nullable=False)

    user = relationship("User", back_populates="words")

    def to_dict(self):
        """
        Преобразует объект слова в словарь.

        Используется для сериализации объекта слова в формат словаря,
        который может быть легко передан или сохранен. Включает информацию
        о слове: ID, текст слова, его перевод и ID пользователя, которому оно принадлежит.

        :return: Словарь с данными слова
        :rtype: dict[str, any]
        """
        return {
            "id": self.id,
            "word": self.word,
            "translation": self.translation,
            "user_id": self.user_id,
        }

    def __str__(self):
        return f"Word {self.word} - > {self.translation}"


class PresetWord(Base):
    __tablename__ = 'preset_words'
    id = Column(Integer, primary_key=True)
    word = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    category = Column(String, nullable=False)

    def __str__(self):
        return f"{self.word} -> {self.translation} ({self.category})"

    def to_dict(self):
        """
        Преобразует объект предустановленного слова в словарь.

        Используется для сериализации объекта предустановленного слова в формат словаря,
        который может быть легко передан или сохранен. Включает информацию о слове:
        ID, текст слова, его перевод и категорию, к которой оно принадлежит.

        :return: Словарь с данными предустановленного слова
        :rtype: dict[str, any]
        """
        return {
            "id": self.id,
            "word": self.word,
            "translation": self.translation,
            "category": self.category
        }


def create_tables(engine):
    """
    Создает все таблицы в базе данных на основе определенных моделей SQLAlchemy.

    Использует метаданные Base для создания таблиц user, words и preset_words
    в базе данных, если они еще не существуют. Выполняет DDL-операции для
    инициализации структуры базы данных при первом запуске приложения.

    :param engine: Объект движка SQLAlchemy для подключения к базе данных
    :type engine: sqlalchemy.engine.Engine
    """
    Base.metadata.create_all(engine)

