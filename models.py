import sqlalchemy
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    CID = Column(Integer, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)

class Words(Base):
    __tablename__ = 'words'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    word = Column(String, nullable=False)
    translation = Column(String, nullable=False)

    user = relationship("User", back_populates="words")