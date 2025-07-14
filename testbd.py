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

# TODO: Инициализация подключения к БД
load_dotenv()
Base = declarative_base()
engine = create_engine(os.getenv('DB_URL'))
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

def get_user(user_id: int) -> Users:
    """
    Получаем пользователя по ID
    :param user_id: ID пользователя
    :return: Объект Users
    """
    return session.query(Users).filter_by(id_VK_user=user_id).first()
    # return session.query(Users).first()


def create_new_user(user_id: int, name: str = None, surname: str = None,
                    age: int = None, gender: str = None, city: str = None):
    new_user = Users(id_VK_user=user_id, name=name, surname=surname, age=age, gender=gender, city=city)
    session.add(new_user)
    session.commit()

def add_favorite(user_id: int, target_id: int):
    """
    Добавление
    :param user_id: ID пользователя
    :param target_id: ID избранного пользователя
    :return:
    """
    # При отсутствии избранного пользователя создаём его
    user = get_user(target_id)
    if not user:
        # Получаем данные об избранном пользователе
        user = VKBot.get_user_info(target_id)
        create_new_user(user['id'], user['first_name'], user['last_name'],
                user['age'], user['sex'], user['city'])
    # Добавление пользователя в избранные
    new_favorite = Favorites(id_VK_user=user_id, id_target=target_id)
    session.add(new_favorite)
    session.commit()

def get_favorites(user_id: int):
    """
    Получение избранных пользователей
    :param user_id:
    :return:
    """
    # favorites =
    pass



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
                print(user)
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