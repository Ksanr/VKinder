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
    id_city = Column(BIGINT, ForeignKey('city.id_city'))                        # ID города проживания пользователя
    interest = relationship('UsersInterest', back_populates='user')
    blacklist = relationship('BlackList', back_populates='user')
    favorite = relationship('Favorites', back_populates='user')
    photo = relationship('Photos', back_populates='user')
    match = relationship('Matches', back_populates='user')
    city = relationship('City', back_populates='user')

    def __repr__(self):
        return f'<User(id_VK_user={self.id_VK_user}, name={self.name}, surname={self.surname}, age={self.age}, gender={self.gender}, city={self.city})>'

    def __str__(self):
        return f'User: id_VK_user={self.id_VK_user}, name={self.name}, surname={self.surname}, age={self.age}, gender={self.gender}, city={self.city}'

class City(Base):
    __tablename__ = 'city'
    id_city = Column(BIGINT, primary_key=True)  # id города
    city_name = Column(VARCHAR)                 # название города
    user = relationship('Users', back_populates='city')

    def __repr__(self):
        return f'<City(id_city={self.id_city}, city_name={self.city_name})>'

    def __str__(self):
        return  f'City: id_city={self.id_city}, city_name={self.city_name}'


class Interests(Base):
    __tablename__ = 'interests'
    id_interest = Column(BIGINT, primary_key=True)  # id интереса
    interest_name = Column(VARCHAR)                 # название интереса
    interest = relationship('UsersInterest', back_populates='interest')

    def __repr__(self):
        return f'<Interests(id_interest={self.id_interest}, interest_name={self.interest_name})>'

    def __str__(self):
        return  f'Interests: id_interest={self.id_interest}, interest_name={self.interest_name}'

class UsersInterest(Base):
    __tablename__ = 'users_interest'
    # id_user_interest = Column(BIGINT, primary_key=True) # id записи
    id_VK_user = Column(BIGINT, ForeignKey('users.id_VK_user'))  # id пользователя ВК
    id_interest = Column(BIGINT, ForeignKey('interests.id_interest'))  # id интереса
    __table_args__ = (PrimaryKeyConstraint('id_VK_user', 'id_interest'),)
    interest = relationship('Interests', back_populates='interest')
    user = relationship('Users', back_populates='interest')

    def __repr__(self):
        return f'<UsersInterest(id_VK_user={self.id_VK_user}, id_interest={self.id_interest})>'

    def __str__(self):
        return f'UsersInterest: id_VK_user={self.id_VK_user}, id_interest={self.id_interest}'

class BlackList(Base):
    __tablename__ = 'blacklist'
    # id_black_user = Column(BIGINT, primary_key=True)    # id записи
    id_VK_user = Column(BIGINT, ForeignKey('users.id_VK_user')) # id пользователя ВК
    id_blocked = Column(BIGINT) # id заблокированного пользователя ВК
    __table_args__ = (PrimaryKeyConstraint('id_VK_user', 'id_blocked'),)
    user = relationship('Users', back_populates='blacklist')

    def __repr__(self):
        return f'<BlackList(id_VK_user={self.id_VK_user}, id_blocked={self.id_blocked})>'

    def __str__(self):
        return f'BlackList: id_VK_user={self.id_VK_user}, id_blocked={self.id_blocked}'


class Favorites(Base):
    __tablename__ = 'favorites'
    # id_favorite_user = Column(BIGINT, primary_key=True)  # id записи
    id_VK_user = Column(BIGINT, ForeignKey('users.id_VK_user')) # id пользователя ВК
    id_target = Column(BIGINT) # id "избранного" пользователя ВК
    __table_args__ = (PrimaryKeyConstraint('id_VK_user', 'id_target'),)
    user = relationship('Users', back_populates='favorite')

    def __repr__(self):
        return f'<Favorites(id_VK_user={self.id_VK_user}, id_target={self.id_target})>'

    def __str__(self):
        return f'Favorites: id_VK_user={self.id_VK_user}, id_target={self.id_target}'

class Photos(Base):
    __tablename__ = 'photos'
    id_user_photo = Column(BIGINT, primary_key=True)   # id записи
    id_VK_user = Column(BIGINT, ForeignKey('users.id_VK_user')) # id пользователя ВК
    url = Column(TEXT)                              # ссылка на фото
    likes = Column(SMALLINT)                        # количество лайков
    attachment = Column(TEXT)                       # аттачмент
    is_profile_photo = Column(Boolean)              # фото стоит на профиле?
    user = relationship('Users', back_populates='photo')

    def __repr__(self):
        return f'<Photos(id_user_photo={self.id_user_photo}, id_VK_user={self.id_VK_user}, url={self.url}, likes={self.likes}, attachment={self.attachment}, is_profile_photo={self.is_profile_photo})>'

    def __str__(self):
        return f'Photos: id_user_photo={self.id_user_photo}, id_VK_user={self.id_VK_user}, url={self.url}, likes={self.likes}, attachment={self.attachment}, is_profile_photo={self.is_profile_photo}'

class Matches(Base):
    __tablename__ = 'matches'
    id_match = Column(BIGINT, primary_key=True)      # id записи совпадения
    id_VK_user = Column(BIGINT, ForeignKey('users.id_VK_user')) # id пользователя ВК - "инициатора"
    id_target_user = Column(BIGINT) # id предлагаемого пользователя
    matched_at = Column(TIMESTAMP)                   # метка добавления совпадения в таблицу
    match_shown = Column(Boolean)                    # Совпадение показано?
    user = relationship('Users', back_populates='match')

    def __repr__(self):
        return f'<Matches(id_match={self.id_match}, id_VK_user={self.id_VK_user}, id_target_user={self.id_target_user}, matched_at={self.matched_at}, match_shown={self.match_shown})>'

    def __str__(self):
        return f'Matches: id_match={self.id_match}, id_VK_user={self.id_VK_user}, id_target_user={self.id_target_user}, matched_at={self.matched_at}, match_shown={self.match_shown}'

if __name__ == '__main__':
# Удаление таблиц, созданных ранее с другим набором полей
# после отладки закомментировать/удалить
    Base.metadata.drop_all(engine)

# Создание таблиц в БД
    Base.metadata.create_all(engine)