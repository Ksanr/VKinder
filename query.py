from datetime import datetime
from dotenv import load_dotenv
import os, logging

from models import Users, Interests, UsersInterest, BlackList, Favorites, Photos, Matches, Gender
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Инициализация подключения к БД
load_dotenv()
Base = declarative_base()
engine = create_engine(os.getenv('DB_URL'))
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

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
                    age: int = None, gender: Gender = None, city: str = None):
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
        # при отсутствии данных можно запросить из ВК
        # if not all((name, surname, age, gender, city)):
        #     print(user_id)
        #     vk_user = VKBot.get_user_info(user_id)
        # name = name or vk_user['first_name']
        # surname = surname or vk_user['last_name']
        # age = age or vk_user['age']
        # gender = gender or vk_user['sex']
        # city = city or vk_user['city']

        user = get_user(user_id)
        if user:
            return f'⚠️ Пользователь с id:{user_id} уже существует в БД'

        new_user = Users(id_VK_user=user_id, name=name, surname=surname, age=age,
                         gender=gender, city=city)
        session.add(new_user)
        session.commit()
        return '✅ Создан новый пользователь.'
    except Exception as e:
        logger.error(f'Ошибка при сохранении пользователя: {e}')
        raise ValueError(f'Ошибка при сохранении пользователя: {e}')


def update_user(user_id: int, name: str = None, surname: str = None,
                    age: int = None, gender: str = None, city: str = None):
    """
    Обновление данных о пользователе
    :param user_id: ID пользователя
    :param name: имя
    :param surname: фамилия
    :param age: возраст
    :param gender: пол
    :param city: город
    :return:
    """
    try:
        user = get_user(user_id)
        if not user:
            return f'😔 Пользователь с id:{user_id} не существует в БД'

        if name: user.name = name
        if surname: user.surname=surname
        if age: user.age = age
        if gender: user.gender = gender
        if city: user.city = city
        session.add(user)
        session.commit()
        return '✅ Данные о пользователе обновлены.'
    except Exception as e:
        logger.error(f'Ошибка при обновлении данных пользователя: {e}')
        raise ValueError(f'Ошибка при обновлении данных пользователя: {e}')

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
        # При отсутствии избранного пользователя можно создать его
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
        logger.error(f'Ошибка при сохранении пользователя в список избранных: {e}')
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
        # При отсутствии пользователя для ЧС можно создать его
        # user = get_user(blocked_id)
        # if not user:
        #     # Получаем данные об пользователе, добавляемом в ЧС
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
                 .filter(Matches.id_VK_user == user_id, Matches.match_shown == False or Matches.match_shown == None)
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
                return interest[0]
            return '😔 Интереса по ID не нашлось.'
        interest = (session.query(Interests.id_interest)
                    .filter_by(interest_name=interest_name)
                    .first())
        if interest:
            return interest[0]
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
        if get_interest(interest_name=interest_name):
            return '⚠️ Данный интерес уже существует в БД'
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
            interests_list = [i[0] for i in interests]
            return interests_list
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
            id_interest = get_interest(interest_name=interest_name)
            if not isinstance(id_interest, int):
                add_interest(interest_name)
                id_interest = get_interest(interest_name=interest_name)
        else:
            interest_name = get_interest(id_interest)
        old_interests = get_user_interest(user_id)
        print(old_interests, id_interest, interest_name)
        if '😔' not in old_interests and interest_name in old_interests:
            return  '⚠️ Данный интерес уже добавлен пользователю в БД'
        new_interest = UsersInterest(id_VK_user=user_id, id_interest=id_interest)
        session.add(new_interest)
        session.commit()
        return '✅ Интерес пользователя успешно добавлен в БД'
    except Exception as e:
        logger.error(f'Ошибка при сохранении интересов пользователя: {e}')
        raise ValueError(f'Ошибка при сохранении интереса пользователя: {e}')

def find_match(user_id: int):
    """
    Поиск совпадений по базе данных
    :param user_id: ID пользователя
    :return:
    """
    try:
        # получаем информацию о пользователе
        user = get_user(user_id)
        if not user:
            return '😔 Не удалось получить информацию о вашем профиле'

        # получаем информацию об интересах пользователя
        user_interests = get_user_interest(user_id)

        # Определяем параметры поиска
        search_sex = (Gender.VALUE_TWO, Gender.VALUE_ONE)[user.gender == Gender.VALUE_TWO]
        age_from = max(18, user.age - 5) if user.age else 18
        age_to = min(80, user.age + 5) if user.age else 35
        city = user.city

        # Поиск пользователей без учёта интересов
        found_users = session.query(Users).filter(Users.gender == search_sex,
                                                  Users.age >= age_from,
                                                  Users.age <= age_to,
                                                  Users.city == city).all()
        if not found_users:
            return '😔 Никого не нашлось. Попробуйте позже'

        # Составляем список из найденных пользователей со схожими интересами
        if '😔' in user_interests:
            interest_users = found_users
        else:
            interest_users = []
            for found_user in found_users:
                for found_user_interest in get_user_interest(found_user.id_VK_user):
                    if found_user_interest in user_interests:
                        interest_users.append(found_user)
                        break

        if not interest_users:
            return '😔 С Вашими интересами никого не нашлось. Попробуйте позже'

        # Сохраняем результат в БД
        for found_user in interest_users: # Можно сохранить пользователей без учёта интересов заменив interest_users на found_users
            # проверяем наличие аналогичных записей, сделанных ранее
            match = session.query(Matches).filter(Matches.id_VK_user == user_id,
                                                  Matches.id_target_user == found_user.id_VK_user).first()
            if not match:
                add_match(user_id, found_user.id_VK_user, datetime.now(), False)

        # Возвращаем первое совпадение
        return get_match(user_id)
    except Exception as e:
        logger.error(f'Ошибка при поиске совпадений: {e}')
        raise ValueError(f'Ошибка при поиске совпадений: {e}')

def get_user_full_info(user_id: int):
    """
    Получение полной информации о пользователе
    :param user_id: ID пользователя
    :return:
    """
    try:
        user = get_user(user_id)
        photos = get_photo(user_id)
        interests = get_user_interest(user_id)

        return {'id_VK_user': user_id,
                'name': user.name,
                'surname': user.surname,
                'age': user.age,
                'gender': user.gender,
                'city': user.city,
                'photos': photos,
                'interests': interests
                }
    except Exception as e:
        logger.error(f'Ошибка при получении полной информации о пользователе: {e}')
        raise ValueError(f'Ошибка при получении полной информации о пользователе: {e}')



def test_bd():
    print(create_new_user(10, 'Иван', 'Иванов', 33,
                          Gender.VALUE_ONE, 'Москва'))
    print(create_new_user(11, 'Петр', 'Петров', 20,
                          Gender.VALUE_ONE, 'Москва'))
    print(create_new_user(12, 'Ася', 'Сидорова', 30,
                          Gender.VALUE_TWO, 'Москва'))
    print(create_new_user(13, 'Вера', 'Воронина', 19,
                          Gender.VALUE_TWO, 'Москва'))
    print(create_new_user(14, 'Катя', 'Катина', 29,
                          Gender.VALUE_TWO, 'Казань'))

    for id in range(10, 15):
        print(get_user(id))

    interests = ('рисование', 'поход', 'танцы')
    for interest in interests:
        print(add_interest(interest))

    for interest in interests:
        print(get_interest(interest_name=interest))

    print(add_user_interest(10, interest_name='рисование'))
    print(add_user_interest(10, interest_name='поход'))
    print(add_user_interest(12, interest_name='поход'))

    for id in range(10, 15):
        print(get_user_full_info(id))

    print('**************** Ищем совпадения *********')
    for id in range(10, 15):
        print(find_match(id))

    print(update_user(11, city='Казань'))
    print(get_user_full_info(11))
    print(get_user_full_info(14))

    print('**************** Ищем совпадения *********')
    for id in range(10, 15):
        print(find_match(id))



if __name__ == '__main__':
    test_bd()


# def write_msg(user_id, message):
#     vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7),})
#

# from random import randrange
# import vk_api
# from vk_api.longpoll import VkLongPoll, VkEventType

# TOKEN = os.getenv('VK_GROUP_TOKEN')
# vk = vk_api.VkApi(token=TOKEN)
# longpoll = VkLongPoll(vk)



# if __name__ == '__main__':
#     for event in longpoll.listen():
#         if event.type == VkEventType.MESSAGE_NEW:
#
#             if event.to_me:
#                 request = event.text
#                 user = get_user(event.user_id)
#                 if not user:
#                     create_new_user(event.user_id)
#
#                     write_msg(event.user_id, f'Приветствую, {event.user_id}, в боте поиска контактов')
#                     print(f'В БД добавлен пользователь {event.user_id}')
#                 elif request == "привет":
#                     write_msg(event.user_id, f"Хай, {event.user_id}")
#                 elif request == "пока":
#                     write_msg(event.user_id, "Пока((")
#                 else:
#                     write_msg(event.user_id, "Не поняла вашего ответа...")