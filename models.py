import sqlalchemy
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


class Word(Base):
    __tablename__ = 'words'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    word = Column(String, nullable=False)
    translation = Column(String, nullable=False)

    user = relationship("User", back_populates="words")

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


def create_tables(engine):
    Base.metadata.create_all(engine)
