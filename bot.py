import os
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from dotenv import load_dotenv
import requests
import json
from typing import List, Dict, Optional
import logging

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

        # TODO: Инициализация подключения к БД
        # self.db = DatabaseManager()

        logger.info("VKinder Bot инициализирован")

    def create_keyboard(self, buttons: List[Dict[str, str]]) -> str:
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
                'id': user_info['id'],
                'first_name': user_info['first_name'],
                'last_name': user_info['last_name'],
                'city': user_info.get('city', {}).get('title', 'Не указан'),
                'age': self._calculate_age(user_info.get('bdate', '')),
                'sex': user_info.get('sex', 0)
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе {user_id}: {e}")
            return None

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
                        'city': user.get('city', {}).get('title', 'Не указан'),
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
            message = f"👤 {user_profile['first_name']} {user_profile['last_name']}\n"
            message += f"📍 {user_profile['city']}\n"
            if user_profile['age']:
                message += f"🎂 {user_profile['age']} лет\n"
            message += f"🔗 {user_profile['profile_url']}"

            # Создаем клавиатуру с кнопками
            keyboard_buttons = [
                {'text': '❤️ В избранное', 'color': 'POSITIVE', 'payload': 'add_favorite'},
                {'text': '➡️ Следующий', 'color': 'PRIMARY', 'payload': 'next_user'},
                {'text': '📋 Избранное', 'color': 'SECONDARY', 'payload': 'show_favorites'},
                {'text': '🔍 Новый поиск', 'color': 'SECONDARY', 'payload': 'new_search'}
            ]

            keyboard = self.create_keyboard(keyboard_buttons)

            # Формируем вложения (фотографии)
            attachments = []
            for photo in photos:
                attachments.append(photo['attachment'])

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

    def add_to_favorites(self, user_id: int, target_user: Dict):
        """
        Добавляет пользователя в избранное
        
        Args:
            user_id: ID пользователя бота
            target_user: Профиль добавляемого пользователя
        """
        try:
            # TODO: Сохранение в БД
            # self.db.add_favorite(user_id, target_user)

            # Временно сохраняем в памяти
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {'favorites': []}

            # Проверяем, не добавлен ли уже
            favorites = self.user_sessions[user_id].get('favorites', [])
            if not any(fav['id'] == target_user['id'] for fav in favorites):
                favorites.append(target_user)
                self.user_sessions[user_id]['favorites'] = favorites

                self.send_message(user_id, "✅ Пользователь добавлен в избранное!")
            else:
                self.send_message(user_id, "⚠️ Этот пользователь уже в избранном!")

        except Exception as e:
            logger.error(f"Ошибка добавления в избранное: {e}")

    def show_favorites(self, user_id: int):
        """
        Показывает список избранных пользователей
        
        Args:
            user_id: ID пользователя бота
        """
        try:
            # TODO: Получение из БД
            # favorites = self.db.get_favorites(user_id)

            # Временно получаем из памяти
            favorites = self.user_sessions.get(user_id, {}).get('favorites', [])

            if not favorites:
                self.send_message(user_id, "📋 Ваш список избранного пуст")
                return

            message = "📋 Избранные пользователи:\n\n"
            for i, fav in enumerate(favorites, 1):
                message += f"{i}. {fav['first_name']} {fav['last_name']}\n"
                message += f"   {fav['profile_url']}\n\n"

            self.send_message(user_id, message)

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
        Начинает поиск пользователей
        
        Args:
            user_id: ID пользователя бота
        """
        try:
            # Получаем информацию о пользователе
            user_info = self.get_user_info(user_id)
            if not user_info:
                self.send_message(user_id, "❌ Не удалось получить информацию о вашем профиле")
                return

            # Определяем параметры поиска
            search_sex = 1 if user_info['sex'] == 2 else 2  # Ищем противоположный пол
            user_age = user_info['age']
            age_from = max(18, user_age - 5) if user_age else 18
            age_to = min(80, user_age + 5) if user_age else 35

            # TODO: Получение ID города из БД или кеша
            city_id = 1  # Москва по умолчанию

            # Поиск пользователей
            found_users = self.search_users(city_id, age_from, age_to, search_sex)

            if not found_users:
                self.send_message(user_id, "😔 Никого не найдено. Попробуйте позже.")
                return

            # Сохраняем результаты поиска в сессию
            self.user_sessions[user_id] = {
                'search_results': found_users,
                'current_index': 0,
                'favorites': self.user_sessions.get(user_id, {}).get('favorites', [])
            }

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
            session = self.user_sessions.get(user_id)
            if not session or 'search_results' not in session:
                self.send_message(user_id, "🔍 Сначала запустите поиск командой /start")
                return

            search_results = session['search_results']
            current_index = session['current_index']

            if current_index >= len(search_results):
                self.send_message(user_id, "🔚 Больше пользователей не найдено. Начните новый поиск.")
                return

            current_user = search_results[current_index]

            # Получаем популярные фотографии
            photos = self.get_popular_photos(current_user['id'])

            # Сохраняем текущего пользователя в сессию
            session['current_user'] = current_user
            session['current_index'] = current_index + 1

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
                    {'text': '❤️ Избранное', 'color': 'SECONDARY', 'payload': 'show_favorites'}
                ]

                keyboard = self.create_keyboard(keyboard_buttons)
                self.send_message(user_id, welcome_message, keyboard)

            elif message == '/favorites':
                self.show_favorites(user_id)

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
                session = self.user_sessions.get(user_id)
                if session and 'current_user' in session:
                    self.add_to_favorites(user_id, session['current_user'])
                else:
                    self.send_message(user_id, "❌ Нет активного пользователя для добавления")

            elif payload == 'show_favorites':
                self.show_favorites(user_id)

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
