from datetime import datetime
from dotenv import load_dotenv
import os, logging

from models import Users, Interests, UsersInterest, BlackList, Favorites, Photos, Matches
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
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

TOKEN = os.getenv('VK_GROUP_TOKEN')
vk = vk_api.VkApi(token=TOKEN)
longpoll = VkLongPoll(vk)

logger = logging.getLogger(__name__)
def get_user(user_id: int):
    """
    Получение пользователя по ID
    :param user_id: ID пользователя
    :return: Объект Users
    """
    try:
        # user = session.query(Users).filter_by(id_VK_user=user_id).first()
        user = session.get(Users, user_id)
        return user
    except Exception as e:
        logger.error(f'Ошибка при получении информации о пользователе: {e}')
        raise ValueError(f'Ошибка при получении информации о пользователе: {e}')

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
        # TODO: при отсутствии данных запросить из ВК
        # if not all((name, surname, age, gender, city)):
        #     print(user_id)
        #     vk_user = VKBot.get_user_info(user_id)
        # name = name or vk_user['first_name']
        # surname = surname or vk_user['last_name']
        # age = age or vk_user['age']
        # gender = gender or vk_user['sex']
        # city = city or vk_user['city']

        new_user = Users(id_VK_user=user_id, name=name, surname=surname, age=age,
                         gender=gender, city=city)
        session.add(new_user)
        session.commit()
        return '✅ Создан новый пользователь.'
    except Exception as e:
        logger.error(f'Ошибка при сохранении пользователя: {e}')
        raise ValueError(f'Ошибка при сохранении пользователя: {e}')

def get_favorites(user_id: int):
    """
    Получение избранных пользователей
    :param user_id: ID пользователя бота
    :return:
    """
    try:
        users = (session.query(Favorites.id_target)
                 .filter_by(id_VK_user=user_id).all())
        if users:
            return users
        return '📋 Ваш список избранного пуст'
    except Exception as e:
        logger.error(f'Ошибка при получении списка избранных: {e}')
        raise ValueError(f'Ошибка при получении списка избранных: {e}')

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
            return '⚠️ Этот пользователь уже в избранном!'
        # TODO: При отсутствии избранного пользователя создать его
        # user = get_user(target_id)
        # if not user:
        #     # Получаем данные об избранном пользователе из ВК
        #     user = VKBot.get_user_info(target_id)
        #     create_new_user(user['id'], user['first_name'], user['last_name'],
        #                     user['age'], user['sex'], user['city'])

        # Добавление пользователя в избранные
        new_favorite = Favorites(id_VK_user=user_id, id_target=target_id)
        session.add(new_favorite)
        session.commit()
        return '✅ Пользователь добавлен в избранное!'
    except Exception as e:
        logger.error(f'Ошибка при cохранении пользователя в список избранных: {e}')
        raise ValueError(f'Ошибка при сохранении пользователя в список избранных: {e}')

def get_blacklist(user_id: int):
    """
    Получение избранных пользователей
    :param user_id: ID пользователя бота
    :return:
    """
    try:
        users = (session.query(BlackList.id_blocked)
                 .filter_by(id_VK_user=user_id)
                 .all())
        if users:
            return users
        return '📋 Ваш чёрный список пуст'
    except Exception as e:
        logger.error(f'Ошибка при получении чёрного списка: {e}')
        raise ValueError(f'Ошибка при получении чёрного списка: {e}')

def add_blacklist(user_id: int, blocked_id: int):
    """
    Добавление пользователя в черный список
    :param user_id: ID пользователя
    :param blocked_id: ID пользователя для блокировки
    :return:
    """
    # проверяем наличие пользователя в чёрном списке
    try:
        if blocked_id in get_blacklist(user_id):
            return '⚠️ Этот пользователь уже в чёрном списке!'
        # TODO: При отсутствии избранного пользователя создать его
        # user = get_user(blocked_id)
        # if not user:
        #     # Получаем данные об избранном пользователе
        #     user = VKBot.get_user_info(blocked_id)
        #     create_new_user(user['id'], user['first_name'], user['last_name'],
        #                     user['age'], user['sex'], user['city'])

        # Добавление пользователя в избранные
        new_black_user = BlackList(id_VK_user=user_id, id_blocked=blocked_id)
        session.add(new_black_user)
        session.commit()
        return '✅ Пользователь добавлен в чёрный список!'
    except Exception as e:
        logger.error(f'Ошибка при сохранении пользователя в чёрный список: {e}')
        raise ValueError(f'Ошибка при сохранении пользователя в чёрный список: {e}')

def get_photo(user_id: int, count: int = 3):
    """
    вызов фото из БД
    :param user_id: ID пользователя
    :param count: количество записей
    :return:
    """
    try:
        photos = (session.query(Photos.url)
                  .filter_by(id_VK_user=user_id)
                  .order_by(Photos.likes)
                  .limit(count)
                  .all())
        return photos
    except Exception as e:
        logger.error(f'Ошибка при получении фото: {e}')
        raise ValueError(f'Ошибка при получении фото: {e}')

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
        new_photo = Photos(id_VK_user=user_id, url=url, likes=likes,
                           is_profile_photo=is_profile_photo)
        session.add(new_photo)
        session.commit()
        return '✅ Фото успешно добавлено'
    except Exception as e:
        logger.error(f'Ошибка при сохранении фото: {e}')
        raise ValueError(f'Ошибка при сохранении фото: {e}')

def get_match(user_id: int):
    """
    вызов совпадения из БД
    :param user_id: ID пользователя
    :return:
    """
    try:
        match = (session.query(Matches)
                 .filter(Matches.id_VK_user == user_id, Matches.match_shown == False)
                 .first())
        if match:
            match.match_shown = True
            session.add(match)
            session.commit()
            return match
        return '😔 Никого не нашлось.'
    except Exception as e:
        logger.error(f'Ошибка при получении совпадений: {e}')
        raise ValueError(f'Ошибка при получении совпадений: {e}')

def add_match(user_id: int, target_id: int, matched_at: datetime = None,
              match_shown: bool = False):
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
        new_match = Matches(id_VK_user=user_id, id_target_user=target_id,
                            matched_at=matched_at)
        session.add(new_match)
        session.commit()
        return '✅ Совпадение успешно добавлено'
    except Exception as e:
        logger.error(f'Ошибка при сохранении совпадений: {e}')
        raise ValueError(f'Ошибка при сохранении совпадения: {e}')

def get_interest(id_interest: int = None, interest_name : str = None):
    """
    Вызов названия/ID интереса
    :param id_interest: ID интереса
    :param interest_name: название интереса
    :return:
    """
    try:
        if id_interest:
            # interest = (session.query(Interests.interest_name)
            #             .filter_by(id_interest=id_interest)
            #             .first())
            interest = session.get(Interests.interest_name, id_interest)
            if interest:
                return interest
            return '😔 Интереса по ID не нашлось.'
        # interest = (session.query(Interests.id_interest)
        #             .filter_by(interest_name=interest_name)
        #             .first())
        interest = session.get(Interests.id_interest, interest_name)
        if interest:
            return interest
        return '😔 Интереса по имени не нашлось.'
    except Exception as e:
        logger.error(f'Ошибка при получении интереса: {e}')
        raise ValueError(f'Ошибка при получении интереса: {e}')

def add_interest(interest_name: str):
    """
    Добавление интереса в БД
    :param interest_name: наименование интереса
    :return:
    """
    try:
        new_interest = Interests(interest_name=interest_name)
        session.add(new_interest)
        session.commit()
        return '✅ Интерес успешно добавлен в БД'
    except Exception as e:
        logger.error(f'Ошибка при сохранении интереса: {e}')
        raise ValueError(f'Ошибка при сохранении интереса: {e}')

def get_user_interest(user_id: int):
    """
    Вызов интересов пользователя
    :param user_id: ID пользователя
    :return:
    """
    try:
        interests = (session.query(Interests.interest_name)
                     .join(UsersInterest).
                     filter(UsersInterest.id_VK_user == user_id).
                     all())
        if interests:
            return interests
        return '😔 У данного пользователя интересов не нашлось.'
    except Exception as e:
        logger.error(f'Ошибка при получении интересов пользователя: {e}')
        raise ValueError(f'Ошибка при получении интересов пользователя: {e}')

def add_user_interest(user_id: int, id_interest: int = None,
                      interest_name: str = None):
    """
    Добавление интереса пользователю
    :param user_id: ID пользователя
    :param id_interest: ID интереса
    :param interest_name: название интереса
    :return:
    """
    if not (id_interest or interest_name):
        return '😔 Не указаны ID или название интереса.'
    try:
        # проверка наличия ID интереса в БД
        if id_interest and '😔' in get_interest(id_interest):
            return '😔 Интереса с таким ID в БД нет. Добавить интерес пользователю невозможно'
        if interest_name:
            id_interest = get_interest(interest_name)
            if '😔' in id_interest:
                add_interest(interest_name)
                id_interest = get_interest(interest_name)
        new_interest = UsersInterest(id_VK_user=user_id, id_interest=id_interest)
        session.add(new_interest)
        session.commit()
        return '✅ Интерес пользователя успешно добавлен в БД'
    except Exception as e:
        logger.error(f'Ошибка при сохранении интересов пользователя: {e}')
        raise ValueError(f'Ошибка при сохранении интереса пользователя: {e}')


def write_msg(user_id, message):
    vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7),})


if __name__ == '__main__':
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:

            if event.to_me:
                request = event.text
                user = get_user(event.user_id)
                if not user:
                    create_new_user(event.user_id)

                    write_msg(event.user_id, f'Приветствую, {event.user_id}, в боте поиска контактов')
                    print(f'В БД добавлен пользователь {event.user_id}')
                elif request == "привет":
                    write_msg(event.user_id, f"Хай, {event.user_id}")
                elif request == "пока":
                    write_msg(event.user_id, "Пока((")
                else:
                    write_msg(event.user_id, "Не поняла вашего ответа...")