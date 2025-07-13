from models import SessionLocal, Users, Interests, UsersInterest, BlackList, Favorites, Photos, Matches
from dotenv import load_dotenv
from sqlalchemy import distinct
import os
from random import randrange
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

load_dotenv()
TOKEN = os.getenv('VK_KEY')
session = SessionLocal()

vk = vk_api.VkApi(token=TOKEN)
longpoll = VkLongPoll(vk)


def write_msg(user_id, message):
    vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7),})

def get_user(user_id):
    """Получаем пользователя по ID"""
    # return session.query(Users).filter_by(id_VK_user=user_id).first()
    return session.query(Users).first()


def create_new_user(user_id, name=None, surname=None, age=None, gender=None, city=None):
    new_user = Users(id_VK_user=user_id, name=name, surname=surname, age=age, gender=gender, city=city)
    session.add(new_user)
    session.commit()

if __name__ == '__main__':
    # запись в БД проходит, а вызов пока не получается. Далее попытки разобраться
    user = get_user(29297928)
    session.commit()
    print(user)

    ask = session.query(Users).all()

    print(ask)
    # конец блока диагностики

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