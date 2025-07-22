import os
from pyexpat.errors import messages

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from dotenv import load_dotenv
import requests
import json
from typing import List, Dict, Optional
import logging
from query import SessionLocal, get_user, create_new_user, update_user, get_favorites, add_favorite, get_blacklist, \
    add_blacklist, get_photo, add_photo, get_match, add_match, get_interest, add_interest, get_user_interest, \
    add_user_interest, find_match, get_user_full_info
from models import Gender

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class VKinderBot:
    """
    Бот для поиска пользователей ВКонтакте для знакомств
    
    Основной функционал:
    - Поиск пользователей по критериям (возраст, пол, город)
    - Получение популярных фотографий профиля
    - Навигация между пользователями
    - Система избранного
    """

    def __init__(self, group_token: str, user_token: str):
        """
        Инициализация бота
        
        Args:
            group_token: Токен группы для отправки сообщений
            user_token: Токен пользователя для поиска людей
        """
        self.group_token = group_token
        self.user_token = user_token

        # Инициализация API для группы (отправка сообщений)
        self.vk_group = vk_api.VkApi(token=group_token)
        self.longpoll = VkLongPoll(self.vk_group)

        # Инициализация API для пользователя (поиск людей)
        self.vk_user = vk_api.VkApi(token=user_token)

        # Состояние пользователей бота
        self.user_sessions = {}

        # Инициализация подключения к БД
        session = SessionLocal()
        # self.db = DatabaseManager()

        logger.info("VKinder Bot инициализирован")

    def create_keyboard(self, buttons: List[Dict[str, str]]) -> dict:
        """
        Создает клавиатуру с кнопками
        
        Args:
            buttons: Список кнопок [{'text': 'Текст', 'color': 'color', 'payload': 'payload'}]
            
        Returns:
            JSON строка клавиатуры
        """
        keyboard = VkKeyboard(one_time=True)

        for i, button in enumerate(buttons):
            if i > 0 and i % 2 == 0:  # Новая строка каждые 2 кнопки
                keyboard.add_line()

            color = getattr(VkKeyboardColor, button.get('color', 'PRIMARY'))
            keyboard.add_button(
                button['text'],
                color=color,
                payload=json.dumps(button.get('payload', button['text']))
            )

        return keyboard.get_keyboard()

    def get_user_info(self, user_id: int) -> Dict:
        """
        Получает информацию о пользователе
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Словарь с информацией о пользователе
        """
        try:
            user_info = self.vk_group.method('users.get', {
                'user_ids': user_id,
                'fields': 'city,age,sex,bdate'
            })[0]

            return {
                'id': user_info.get('id', 0),
                'first_name': user_info.get('first_name', 'Скрыто'),
                'last_name': user_info.get('last_name', 'Скрыто'),
                'city': user_info.get('city', {'id': 1, 'title': 'Москва'}),
                'age': self._calculate_age(user_info.get('bdate', '')),
                'sex': user_info.get('sex', 0)
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе {user_id}: {e}")
            return

    def _calculate_age(self, bdate: str) -> int:
        """
        Вычисляет возраст по дате рождения
        
        Args:
            bdate: Дата рождения в формате DD.MM.YYYY
            
        Returns:
            Возраст в годах
        """
        if not bdate or bdate.count('.') < 2:
            return 0

        try:
            from datetime import datetime
            birth_date = datetime.strptime(bdate, '%d.%m.%Y')
            today = datetime.now()
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except:
            return 0

    def search_users(self, city_id: int, age_from: int, age_to: int, sex: int, count: int = 20) -> List[Dict]:
        """
        Поиск пользователей по критериям
        
        Args:
            city_id: ID города
            age_from: Возраст от
            age_to: Возраст до
            sex: Пол (1 - женский, 2 - мужской)
            count: Количество результатов
            
        Returns:
            Список найденных пользователей
        """
        try:
            results = self.vk_user.method('users.search', {
                'city': city_id,
                'age_from': age_from,
                'age_to': age_to,
                'sex': sex,
                'status': 6,  # В активном поиске
                'count': count,
                'fields': 'city,age,sex,bdate'
            })

            users = []
            for user in results['items']:
                if not user.get('is_closed', False):  # Только открытые профили
                    users.append({
                        'id': user['id'],
                        'first_name': user['first_name'],
                        'last_name': user['last_name'],
                        'city': user.get('city', {'id': 1, 'title': 'Москва'}),
                        'age': self._calculate_age(user.get('bdate', '')),
                        'profile_url': f"https://vk.com/id{user['id']}"
                    })

            logger.info(f"Найдено пользователей: {len(users)}")
            return users

        except Exception as e:
            logger.error(f"Ошибка поиска пользователей: {e}")
            return []

    def get_popular_photos(self, user_id: int, count: int = 3) -> List[Dict]:
        """
        Получает самые популярные фотографии пользователя
        
        Args:
            user_id: ID пользователя
            count: Количество фотографий
            
        Returns:
            Список популярных фотографий
        """
        try:
            photos = self.vk_user.method('photos.get', {
                'owner_id': user_id,
                'album_id': 'profile',
                'extended': 1,
                'count': 200  # Получаем больше фото для анализа
            })

            if not photos['items']:
                return []

            # Сортируем по количеству лайков
            sorted_photos = sorted(
                photos['items'],
                key=lambda x: x.get('likes', {}).get('count', 0),
                reverse=True
            )

            popular_photos = []
            for photo in sorted_photos[:count]:
                # Получаем URL максимального размера
                sizes = photo.get('sizes', [])
                if sizes:
                    max_size = max(sizes, key=lambda x: x['width'] * x['height'])
                    popular_photos.append({
                        'id': photo['id'],
                        'owner_id': photo['owner_id'],
                        'url': max_size['url'],
                        'likes': photo.get('likes', {}).get('count', 0),
                        'attachment': f"photo{photo['owner_id']}_{photo['id']}"
                    })

            return popular_photos

        except Exception as e:
            logger.error(f"Ошибка получения фотографий пользователя {user_id}: {e}")
            return []

    def send_user_profile(self, user_id: int, user_profile: Dict, photos: List[Dict]):
        """
        Отправляет профиль пользователя в чат

        Args:
            user_id: ID пользователя
            user_profile: Профиль пользователя
            photos: Список фотографий
        """
        try:
            # Формируем сообщение
            message = f"👤 {user_profile.name} {user_profile.surname}\n"
            message += f"📍 {user_profile.city.city_name}\n"
            if user_profile.age:
                message += f"🎂 {user_profile.age} лет\n"

            # Создаем клавиатуру с кнопками
            keyboard_buttons = [
                {'text': '❤️ В избранное', 'color': 'POSITIVE', 'payload': 'add_favorite'},
                {'text': '🙈 В ЧС', 'color': 'NEGATIVE', 'payload': 'add_blacklist'},
                {'text': '➡️ Следующий', 'color': 'PRIMARY', 'payload': 'next_user'},
                {'text': '📋 Избранное', 'color': 'SECONDARY', 'payload': 'show_favorites'},
                {'text': '🔕 Черный список', 'color': 'SECONDARY', 'payload': 'show_blacklist'},
                {'text': '🔍 Новый поиск', 'color': 'SECONDARY', 'payload': 'new_search'}
            ]

            keyboard = self.create_keyboard(keyboard_buttons)

            # Формируем вложения (фотографии)
            attachments = []
            for photo in photos:
                attachments.append(photo.attachment)

            # Отправляем сообщение
            self.vk_group.method('messages.send', {
                'user_id': user_id,
                'message': message,
                'keyboard': keyboard,
                'attachment': ','.join(attachments) if attachments else None,
                'random_id': get_random_id()
            })

        except Exception as e:
            logger.error(f"Ошибка отправки профиля: {e}")

    def add_to_favorites(self, user_id: int, target_user: dict):
        """
        Добавляет пользователя в избранное
        
        Args:
            user_id: ID пользователя бота
            target_user: Профиль добавляемого пользователя
        """
        try:
            # Сохранение в БД
            message = add_favorite(user_id, target_user.id_VK_user)

            # Создаем клавиатуру с кнопками
            keyboard_buttons = [
                {'text': '➡️ Следующий', 'color': 'PRIMARY', 'payload': 'next_user'},
                {'text': '📋 Избранное', 'color': 'SECONDARY', 'payload': 'show_favorites'},
                {'text': '🔕 Черный список', 'color': 'SECONDARY', 'payload': 'show_blacklist'},
                {'text': '🔍 Новый поиск', 'color': 'SECONDARY', 'payload': 'new_search'}
            ]

            keyboard = self.create_keyboard(keyboard_buttons)

            # Отправляем сообщение
            self.vk_group.method('messages.send', {
                'user_id': user_id,
                'message': message,
                'keyboard': keyboard,
                'random_id': get_random_id()
            })

        except Exception as e:
            logger.error(f"Ошибка добавления в избранное: {e}")

    def show_favorites(self, user_id: int):
        """
        Показывает список избранных пользователей
        
        Args:
            user_id: ID пользователя бота
        """
        try:
            # Получение из БД
            favorites = get_favorites(user_id)

            if isinstance(favorites, str):
                message = "📋 Ваш список избранного пуст"
            else:
                message = "📋 Избранные пользователи:\n\n"
                for i, fav in enumerate(favorites, 1):
                    cur_fav = get_user(fav[0])
                    message += f"{i}. {cur_fav.name} {cur_fav.surname}\n"
                    message += f"   https://vk.com/id{cur_fav.id_VK_user}\n\n"

            keyboard_buttons = [
                {'text': '🔍 Начать поиск', 'color': 'POSITIVE', 'payload': 'start_search'},
                {'text': '❤️ Избранное', 'color': 'SECONDARY', 'payload': 'show_favorites'},
                {'text': '🔕 Черный список', 'color': 'SECONDARY', 'payload': 'show_blacklist'}
            ]

            keyboard = self.create_keyboard(keyboard_buttons)

            self.send_message(user_id, message, keyboard)

        except Exception as e:
            logger.error(f"Ошибка показа избранного: {e}")

    def add_to_blacklist(self, user_id: int, target_user: dict):
        """
        Добавляет пользователя в ЧС

        Args:
            user_id: ID пользователя бота
            target_user: Профиль добавляемого пользователя
        """
        try:
            # Сохранение в БД
            message = add_blacklist(user_id, target_user.id_VK_user)

            # Создаем клавиатуру с кнопками
            keyboard_buttons = [
                {'text': '➡️ Следующий', 'color': 'PRIMARY', 'payload': 'next_user'},
                {'text': '📋 Избранное', 'color': 'SECONDARY', 'payload': 'show_favorites'},
                {'text': '🔕 Черный список', 'color': 'SECONDARY', 'payload': 'show_blacklist'},
                {'text': '🔍 Новый поиск', 'color': 'SECONDARY', 'payload': 'new_search'}
            ]

            keyboard = self.create_keyboard(keyboard_buttons)

            # Отправляем сообщение
            self.vk_group.method('messages.send', {
                'user_id': user_id,
                'message': message,
                'keyboard': keyboard,
                'random_id': get_random_id()
            })

        except Exception as e:
            logger.error(f"Ошибка добавления в избранное: {e}")

    def show_blacklist(self, user_id: int):
        """
        Показывает список пользователей в ЧС

        Args:
            user_id: ID пользователя бота
        """
        try:
            # Получение из БД
            blacklist = get_blacklist(user_id)

            if isinstance(blacklist, str):
                message = "📋 Ваш черный список пуст"
            else:
                message = "📋 пользователи в черном списке:\n\n"
                for i, fav in enumerate(blacklist, 1):
                    cur_fav = get_user(fav[0])
                    message += f"{i}. {cur_fav.name} {cur_fav.surname}\n"
                    message += f"   https://vk.com/id{cur_fav.id_VK_user}\n\n"

            keyboard_buttons = [
                {'text': '🔍 Начать поиск', 'color': 'POSITIVE', 'payload': 'start_search'},
                {'text': '❤️ Избранное', 'color': 'SECONDARY', 'payload': 'show_favorites'},
                {'text': '🔕 Черный список', 'color': 'SECONDARY', 'payload': 'show_blacklist'}
            ]

            keyboard = self.create_keyboard(keyboard_buttons)

            self.send_message(user_id, message, keyboard)

        except Exception as e:
            logger.error(f"Ошибка показа избранного: {e}")

    def send_message(self, user_id: int, message: str, keyboard: str = None):
        """
        Отправляет сообщение пользователю
        
        Args:
            user_id: ID пользователя
            message: Текст сообщения
            keyboard: Клавиатура (JSON)
        """
        try:
            params = {
                'user_id': user_id,
                'message': message,
                'random_id': get_random_id()
            }

            if keyboard:
                params['keyboard'] = keyboard

            self.vk_group.method('messages.send', params)

        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")

    def start_search(self, user_id: int):
        """
        Поиск пользователей в БД

        Args:
            user_id: ID пользователя бота
        """
        try:
            # Получаем информацию о пользователе
            user_info = self.get_user_info(user_id)
            if not user_info:
                self.send_message(user_id, "❌ Не удалось получить информацию о вашем профиле")
                return

            # поиск по БД среди участников чата
            found_users = find_match(user_id)

            if isinstance(found_users, str):
                self.send_message(user_id, found_users)
                return

            # Показываем первого пользователя
            self.show_next_user(user_id)

        except Exception as e:
            logger.error(f"Ошибка начала поиска: {e}")
            self.send_message(user_id, "❌ Ошибка при поиске. Попробуйте позже.")

    def show_next_user(self, user_id: int):
        """
        Показывает следующего пользователя из результатов поиска

        Args:
            user_id: ID пользователя бота
        """
        try:
            match = get_match(user_id)
            if isinstance(match, str):
                keyboard_buttons = [
                    {'text': '🔍 Начать поиск', 'color': 'POSITIVE', 'payload': 'start_search'},
                    {'text': '❤️ Избранное', 'color': 'SECONDARY', 'payload': 'show_favorites'},
                    {'text': '🔕 Черный список', 'color': 'SECONDARY', 'payload': 'show_blacklist'}
                ]

                keyboard = self.create_keyboard(keyboard_buttons)
                self.send_message(user_id, match, keyboard)
                return

            current_user = get_user(match.id_target_user)
            photos = get_photo(match.id_target_user)
            self.user_sessions[user_id] = {
                'current_user': current_user
            }

            # Отправляем профиль
            self.send_user_profile(user_id, current_user, photos)

        except Exception as e:
            logger.error(f"Ошибка показа следующего пользователя: {e}")

    def handle_message(self, event):
        """
        Обработчик входящих сообщений
        
        Args:
            event: Событие VK LongPoll
        """
        try:
            user_id = event.user_id
            message = event.text.lower()

            # проверяем наличие пользователя в БД
            user = get_user(user_id)
            if not user:
                user_VK = self.get_user_info(user_id)

                create_new_user(user_id, user_VK['first_name'], user_VK['last_name'], user_VK['age'],
                                (0, Gender.VALUE_TWO, Gender.VALUE_ONE)[user_VK['sex']], user_VK['city'])

                photos = self.get_popular_photos(user_id)
                for photo in photos:
                    add_photo(user_id, photo['url'], photo['likes'], photo['attachment'], False)

            # Обработка команд
            if message == '/start' or message == 'начать':
                welcome_message = """
🎉 Добро пожаловать в VKinder!

Этот бот поможет вам найти интересных людей для знакомства.

📋 Доступные команды:
• /start - Начать поиск
• /favorites - Показать избранное
• /help - Помощь

Нажмите кнопку ниже, чтобы начать поиск!
                """

                keyboard_buttons = [
                    {'text': '🔍 Начать поиск', 'color': 'POSITIVE', 'payload': 'start_search'},
                    {'text': '❤️ Избранное', 'color': 'SECONDARY', 'payload': 'show_favorites'},
                    {'text': '🔕 Черный список', 'color': 'SECONDARY', 'payload': 'show_blacklist'}
                ]

                keyboard = self.create_keyboard(keyboard_buttons)
                self.send_message(user_id, welcome_message, keyboard)

            elif message == '/favorites':
                self.show_favorites(user_id)

            elif message == '/blacklist':
                self.show_blacklist(user_id)

            elif message == '/help':
                help_message = """
🤖 Помощь по VKinder Bot

📋 Команды:
• /start - Начать работу с ботом
• /favorites - Показать избранных пользователей
• /help - Показать это сообщение

🔘 Кнопки:
• 🔍 Начать поиск - Найти новых людей
• ➡️ Следующий - Показать следующего пользователя
• ❤️ В избранное - Добавить в избранное
• 🙈️ В ЧС - Добавить в черный список
• 📋 Избранное - Показать список избранных

❗ Примечание: Для работы бота требуется открытый профиль ВКонтакте.
                """
                self.send_message(user_id, help_message)

            else:
                # Обработка нераспознанных команд
                self.send_message(user_id, "❓ Команда не распознана. Используйте /help для получения списка команд.")

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")

    def handle_button_click(self, event):
        """
        Обработчик нажатий на кнопки
        
        Args:
            event: Событие VK LongPoll
        """
        try:
            user_id = event.user_id
            payload = json.loads(event.payload)

            if payload == 'start_search':
                self.start_search(user_id)

            elif payload == 'next_user':
                self.show_next_user(user_id)

            elif payload == 'add_favorite':
                user_session = self.user_sessions.get(user_id)
                if user_session and 'current_user' in user_session:
                    self.add_to_favorites(user_id, user_session['current_user'])
                else:
                    self.send_message(user_id, "❌ Нет активного пользователя для добавления")

            elif payload == 'add_blacklist':
                user_session = self.user_sessions.get(user_id)
                if user_session and 'current_user' in user_session:
                    self.add_to_blacklist(user_id, user_session['current_user'])
                else:
                    self.send_message(user_id, "❌ Нет активного пользователя для добавления")

            elif payload == 'show_favorites':
                self.show_favorites(user_id)

            elif payload == 'show_blacklist':
                self.show_blacklist(user_id)

            elif payload == 'new_search':
                self.start_search(user_id)

        except Exception as e:
            logger.error(f"Ошибка обработки нажатия кнопки: {e}")

    def run(self):
        """
        Запуск бота
        """
        logger.info("Запуск VKinder Bot...")

        try:
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    if hasattr(event, 'payload'):
                        # Обработка нажатий кнопок
                        self.handle_button_click(event)
                    else:
                        # Обработка текстовых сообщений
                        self.handle_message(event)

        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")


def main():
    """
    Главная функция запуска бота
    """
    # Получаем токены из переменных окружения
    GROUP_TOKEN = os.getenv('VK_GROUP_TOKEN')
    USER_TOKEN = os.getenv('VK_USER_TOKEN')

    if not GROUP_TOKEN or not USER_TOKEN:
        logger.error("Отсутствуют токены VK. Установите переменные окружения VK_GROUP_TOKEN и VK_USER_TOKEN")
        return

    # Создаем и запускаем бота
    bot = VKinderBot(GROUP_TOKEN, USER_TOKEN)
    bot.run()


if __name__ == "__main__":
    main()
