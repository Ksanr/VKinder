import enum

from sqlalchemy import create_engine, Column, VARCHAR, ForeignKey, BIGINT, SMALLINT, TEXT, Boolean, TIMESTAMP, PrimaryKeyConstraint
from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.types import Enum as SQLEnum
import os

load_dotenv()

Base = declarative_base()
engine = create_engine(os.getenv('DB_URL'))
SessionLocal = sessionmaker(bind=engine)

class Gender(enum.Enum):
    VALUE_ONE = 'мужской'
    VALUE_TWO = 'женский'

class Users(Base):
    __tablename__ = 'users'
    id_VK_user = Column(BIGINT, primary_key=True)   # id пользователя ВК
    name = Column(VARCHAR)                          # имя пользователя
    surname = Column(VARCHAR)                       # фамилия пользователя
    age = Column(SMALLINT)                          # возраст пользователя
    gender = Column(SQLEnum(Gender))                # пол пользователя
    city = Column(VARCHAR)                          # город проживания пользователя
    interest = relationship('UsersInterest', back_populates='user')
    blacklist = relationship('BlackList', back_populates='user')
    favorite = relationship('Favorites', back_populates='user')
    photo = relationship('Photos', back_populates='user')
    match = relationship('Matches', back_populates='user')

class Interests(Base):
    __tablename__ = 'interests'
    id_interest = Column(BIGINT, primary_key=True)  # id интереса
    interest_name = Column(VARCHAR)                 # название интереса
    interest = relationship('UsersInterest', back_populates='interest')

class UsersInterest(Base):
    __tablename__ = 'users_interest'
    # id_user_interest = Column(BIGINT, primary_key=True) # id записи
    id_VK_user = Column(BIGINT, ForeignKey('users.id_VK_user'))  # id пользователя ВК
    id_interest = Column(BIGINT, ForeignKey('interests.id_interest'))  # id интереса
    __table_args__ = (PrimaryKeyConstraint('id_VK_user', 'id_interest'),)
    interest = relationship('Interests', back_populates='interest')
    user = relationship('Users', back_populates='interest')

class BlackList(Base):
    __tablename__ = 'blacklist'
    # id_black_user = Column(BIGINT, primary_key=True)    # id записи
    id_VK_user = Column(BIGINT, ForeignKey('users.id_VK_user')) # id пользователя ВК
    id_blocked = Column(BIGINT) # id заблокированного пользователя ВК
    __table_args__ = (PrimaryKeyConstraint('id_VK_user', 'id_blocked'),)
    user = relationship('Users', back_populates='blacklist')

class Favorites(Base):
    __tablename__ = 'favorites'
    # id_favorite_user = Column(BIGINT, primary_key=True)  # id записи
    id_VK_user = Column(BIGINT, ForeignKey('users.id_VK_user')) # id пользователя ВК
    id_target = Column(BIGINT) # id "избранного" пользователя ВК
    __table_args__ = (PrimaryKeyConstraint('id_VK_user', 'id_target'),)
    user = relationship('Users', back_populates='favorite')

class Photos(Base):
    __tablename__ = 'photos'
    id_user_photo = Column(BIGINT, primary_key=True)   # id записи
    id_VK_user = Column(BIGINT, ForeignKey('users.id_VK_user')) # id пользователя ВК
    url = Column(TEXT)                              # ссылка на фото
    likes = Column(SMALLINT)                        # количество лайков
    is_profile_photo = Column(Boolean)              # фото стоит на профиле?
    user = relationship('Users', back_populates='photo')

class Matches(Base):
    __tablename__ = 'matches'
    id_match = Column(BIGINT, primary_key=True)      # id записи совпадения
    id_VK_user = Column(BIGINT, ForeignKey('users.id_VK_user')) # id пользователя ВК - "инициатора"
    id_target_user = Column(BIGINT) # id предлагаемого пользователя
    matched_at = Column(TIMESTAMP)                   # метка добавления совпадения в таблицу
    match_shown = Column(Boolean)                    # Совпадение показано?
    user = relationship('Users', back_populates='match')



# Удаление таблиц, созданных ранее с другим набором полей
# после отладки закомментировать/удалить
Base.metadata.drop_all(engine)

# Создание таблиц в БД
Base.metadata.create_all(engine)