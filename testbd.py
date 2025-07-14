from datetime import datetime

from models import Users, Interests, UsersInterest, BlackList, Favorites, Photos, Matches
from sqlalchemy import create_engine, distinct
from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.types import Enum as SQLEnum
import os
from bot import VKinderBot as VKBot


from random import randrange
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

# Инициализация подключения к БД
load_dotenv()
Base = declarative_base()
engine = create_engine(os.getenv('DB_URL'))
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

def get_user(user_id: int) -> Users:
    """
    Получение пользователя по ID
    :param user_id: ID пользователя
    :return: Объект Users
    """
    try:
        user = session.query(Users).filter_by(id_VK_user=user_id).first()
        return user
    except Exception as e:
        return "❌ Ошибка при получении информации о пользователе из БД"

def create_new_user(user_id: int, name: str = None, surname: str = None,
                    age: int = None, gender: str = None, city: str = None):
    """
    Создание нового пользователя
    :param user_id: ID пользователя
    :param name: имя
    :param surname: фамилия
    :param age: возраст
    :param gender: пол
    :param city: город
    :return:
    """
    try:
        new_user = Users(id_VK_user=user_id, name=name, surname=surname, age=age,
                         gender=gender, city=city)
        session.add(new_user)
        session.commit()
    except Exception as e:
        return "❌ Ошибка при сохранении пользователя в БД"

def get_favorites(user_id: int):
    """
    Получение избранных пользователей
    :param user_id: ID пользователя бота
    :return:
    """
    try:
        users = session.query(Favorites.id_target).filter_by(id_VK_user=user_id).all()
        if users:
            return users
        return "📋 Ваш список избранного пуст"
    except Exception as e:
        return "❌ Ошибка при получении списка избранных из БД"

def add_favorite(user_id: int, target_id: int):
    """
    Добавление пользователя в избранные
    :param user_id: ID пользователя
    :param target_id: ID избранного пользователя
    :return:
    """
    # проверяем наличие избранного в избранных
    try:
        if target_id in get_favorites(user_id):
            return "⚠️ Этот пользователь уже в избранном!"
        # При отсутствии избранного пользователя создаём его
        user = get_user(target_id)
        if not user:
            # Получаем данные об избранном пользователе из ВК
            user = VKBot.get_user_info(target_id)
            create_new_user(user['id'], user['first_name'], user['last_name'],
                            user['age'], user['sex'], user['city'])
        # Добавление пользователя в избранные
        new_favorite = Favorites(id_VK_user=user_id, id_target=target_id)
        session.add(new_favorite)
        session.commit()
        return "✅ Пользователь добавлен в избранное!"
    except Exception as e:
        return "❌ Ошибка при сохранении пользователя в список избранных в БД"

def get_blacklist(user_id: int):
    """
    Получение избранных пользователей
    :param user_id: ID пользователя бота
    :return:
    """
    try:
        users = session.query(BlackList.id_blocked).filter_by(id_VK_user=user_id).all()
        if users:
            return users
        return "📋 Ваш чёрный список пуст"
    except Exception as e:
        return "❌ Ошибка при получении чёрного списка из БД"

def add_blacklist(user_id: int, blocked_id: int):
    """
    Добавление пользователя в черный список
    :param user_id: ID пользователя
    :param target_id: ID пользователя для блокировки
    :return:
    """
    # проверяем наличие пользователя в чёрном списке
    try:
        if blocked_id in get_blacklist(user_id):
            return "⚠️ Этот пользователь уже в чёрном списке!"
        # При отсутствии избранного пользователя создаём его
        user = get_user(blocked_id)
        if not user:
            # Получаем данные об избранном пользователе
            user = VKBot.get_user_info(blocked_id)
            create_new_user(user['id'], user['first_name'], user['last_name'],
                            user['age'], user['sex'], user['city'])
        # Добавление пользователя в избранные
        new_black_user = BlackList(id_VK_user=user_id, id_blocked=blocked_id)
        session.add(new_black_user)
        session.commit()
        return "✅ Пользователь добавлен в чёрный список!"
    except Exception as e:
        return "❌ Ошибка при сохранении пользователя в чёрный список в БД"

def get_photo(user_id: int, count: int = 3):
    """
    вызов фото из БД
    :param user_id: ID пользователя
    :param count: количество записей
    :return:
    """
    try:
        photos = session.query(Photos.url).filter_by(id_VK_user=user_id).order_by(Photos.likes).limit(count).all()
        return photos
    except Exception as e:
        return "❌ Ошибка при получении фото из БД"

def add_photo(user_id: int, url: str, likes: int, is_profile_photo: bool):
    """
    сохранение фото в БД
    :param user_id: ID пользователя
    :param url: url фото
    :param likes: количество лайков
    :param is_profile_photo: фото профиля
    :return:
    """
    try:
        new_photo = Photos(id_VK_user=user_id, url=url, likes=likes, is_profile_photo=is_profile_photo)
        session.add(new_photo)
        session.commit()
    except Exception as e:
        return "❌ Ошибка при сохранении фото в БД"

def get_match(user_id: int):
    """
    вызов совпадения из БД
    :param user_id: ID пользователя
    :return:
    """
    try:
        match = session.query(Matches).filter(Matches.id_VK_user == user_id, Matches.match_shown == False).first()
        if match:
            match.match_shown = True
            session.commit()
            return match
        return '😔 Никого не нашлось.'
    except Exception as e:
        return "❌ Ошибка при получении совпадений из БД"

def add_match(user_id: int, target_id: int, matched_at: datetime = None, match_shown: bool = False):
    """
    Добавление совпадения в БД
    :param user_id: ID пользователя
    :param target_id: ID совпадающего пользователя
    :param matched_at: Дата и время добавления
    :param match_shown: Совпадение уже показывали
    :return:
    """
    try:
        if not matched_at:
            matched_at = datetime.now()
        new_match = Matches(id_VK_user=user_id, id_target_user=target_id, matched_at=matched_at)
        session.add(new_match)
        session.commit()
    except Exception as e:
        return "❌ Ошибка при сохранении совпадения в БД"

def write_msg(user_id, message):
    vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7),})


if __name__ == '__main__':
    TOKEN = os.getenv('VK_GROUP_TOKEN')
    vk = vk_api.VkApi(token=TOKEN)
    longpoll = VkLongPoll(vk)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:

            if event.to_me:
                request = event.text
                user = get_user(event.user_id)
                if not user:
                    create_new_user(event.user_id)

                    write_msg(event.user_id, f"Приветствую, {event.user_id}, в боте поиска контактов")
                    print(f'В БД добавлен пользователь {event.user_id}')
                elif request == "привет":
                    write_msg(event.user_id, f"Хай, {event.user_id}")
                elif request == "пока":
                    write_msg(event.user_id, "Пока((")
                else:
                    write_msg(event.user_id, "Не поняла вашего ответа...")