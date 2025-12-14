"""
База данных для чат-бота
"""

import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import asynccontextmanager

DATABASE_PATH = "chatbot.db"


@asynccontextmanager
async def get_db():
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_database():
    """Инициализация базы данных"""
    async with get_db() as db:
        # Интенты (намерения пользователя)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS intents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Паттерны (примеры фраз)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intent_id INTEGER NOT NULL,
                pattern TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (intent_id) REFERENCES intents(id) ON DELETE CASCADE
            )
        """)

        # Ответы
        await db.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intent_id INTEGER NOT NULL,
                response TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (intent_id) REFERENCES intents(id) ON DELETE CASCADE
            )
        """)

        # История диалогов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                intent TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Обратная связь
        await db.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                is_helpful INTEGER NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)

        # Неизвестные запросы (для обучения)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS unknown_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.commit()

        # Проверяем, есть ли данные
        cursor = await db.execute("SELECT COUNT(*) FROM intents")
        count = (await cursor.fetchone())[0]

        if count == 0:
            await add_default_intents(db)

        print("✅ База данных чат-бота инициализирована")


async def add_default_intents(db):
    """Добавление базовых интентов"""

    intents_data = [
        {
            "name": "greeting",
            "description": "Приветствие",
            "patterns": [
                "привет", "здравствуй", "здравствуйте", "добрый день",
                "добрый вечер", "доброе утро", "хай", "хеллоу", "hello",
                "hi", "приветствую", "здорово", "салют", "ку", "йо"
            ],
            "responses": [
                "Привет! 👋 Чем могу помочь?",
                "Здравствуйте! Рад вас видеть! 😊",
                "Привет! Как дела?",
                "Добрый день! Чем могу быть полезен?",
                "Приветствую! Задавайте ваши вопросы!"
            ]
        },
        {
            "name": "goodbye",
            "description": "Прощание",
            "patterns": [
                "пока", "до свидания", "прощай", "увидимся",
                "до встречи", "всего доброго", "bye", "goodbye",
                "бай", "удачи", "всего хорошего", "до скорого"
            ],
            "responses": [
                "До свидания! 👋 Хорошего дня!",
                "Пока! Буду рад помочь снова!",
                "Удачи! До новых встреч! 😊",
                "Всего доброго! Заходите ещё!",
                "До скорого! Берегите себя!"
            ]
        },
        {
            "name": "thanks",
            "description": "Благодарность",
            "patterns": [
                "спасибо", "благодарю", "thanks", "thank you",
                "спс", "пасиб", "благодарствую", "мерси",
                "очень признателен", "большое спасибо"
            ],
            "responses": [
                "Пожалуйста! 😊 Обращайтесь!",
                "Рад был помочь!",
                "Не за что! Всегда готов помочь!",
                "Обращайтесь, если что!",
                "Всегда пожалуйста! 🙂"
            ]
        },
        {
            "name": "how_are_you",
            "description": "Как дела",
            "patterns": [
                "как дела", "как ты", "как поживаешь", "что нового",
                "как жизнь", "как сам", "how are you", "как настроение",
                "как оно", "чё как"
            ],
            "responses": [
                "Отлично! Спасибо, что спросили! 😊 А у вас?",
                "Хорошо! Готов помогать! Как ваши дела?",
                "Прекрасно! Работаю и учусь новому!",
                "Всё супер! Чем могу помочь?",
                "Замечательно! Рад общению с вами!"
            ]
        },
        {
            "name": "name",
            "description": "Имя бота",
            "patterns": [
                "как тебя зовут", "твое имя", "кто ты", "ты кто",
                "представься", "как твое имя", "имя", "твоё имя",
                "what is your name", "who are you"
            ],
            "responses": [
                "Меня зовут ChatBot! 🤖 Я ваш умный помощник!",
                "Я ChatBot — AI ассистент, готовый помочь!",
                "ChatBot к вашим услугам! 😊",
                "Я умный чат-бот! Можете звать меня ChatBot!"
            ]
        },
        {
            "name": "help",
            "description": "Помощь",
            "patterns": [
                "помоги", "помощь", "help", "что ты умеешь",
                "что можешь", "твои возможности", "функции",
                "как пользоваться", "инструкция", "команды"
            ],
            "responses": [
                "Я могу:\n• Отвечать на вопросы\n• Поддержать беседу\n• Помочь с информацией\n\nПросто напишите ваш вопрос! 😊",
                "Я умный ассистент! Могу общаться, отвечать на вопросы и помогать. Спрашивайте!",
                "Задавайте любые вопросы — постараюсь помочь! 🤖"
            ]
        },
        {
            "name": "age",
            "description": "Возраст бота",
            "patterns": [
                "сколько тебе лет", "твой возраст", "когда ты родился",
                "сколько лет", "how old are you", "какой твой возраст"
            ],
            "responses": [
                "Я только что родился, но уже много знаю! 🤖",
                "Возраст — это просто цифры! Я молод душой 😄",
                "Мне столько лет, сколько существует этот сервер!"
            ]
        },
        {
            "name": "weather",
            "description": "Погода",
            "patterns": [
                "какая погода", "погода", "weather", "прогноз погоды",
                "что с погодой", "какая температура", "тепло ли",
                "холодно ли", "будет дождь"
            ],
            "responses": [
                "К сожалению, я пока не подключен к погодным сервисам 🌤️ Но могу посоветовать посмотреть на weather.com!",
                "Для точного прогноза рекомендую Яндекс.Погода или Gismeteo! ☀️",
                "Погоду лучше узнать в специализированных сервисах. Я больше по общению! 😊"
            ]
        },
        {
            "name": "time",
            "description": "Время",
            "patterns": [
                "который час", "сколько времени", "время",
                "what time", "текущее время", "подскажи время"
            ],
            "responses": [
                "Посмотрите на часы в углу экрана! ⏰ Я не отслеживаю время.",
                "Время — деньги! 💰 Проверьте на своём устройстве.",
                "Для точного времени используйте time.is! ⏰"
            ]
        },
        {
            "name": "joke",
            "description": "Шутка",
            "patterns": [
                "расскажи шутку", "анекдот", "пошути", "смешное",
                "рассмеши", "joke", "tell me a joke", "юмор"
            ],
            "responses": [
                "Почему программисты путают Хэллоуин и Рождество? Потому что OCT 31 = DEC 25! 🎃😄",
                "— Официант, у вас есть сосиска в тесте?\n— Есть!\n— Пусть сдаёт, не подсказывайте! 😂",
                "Чем отличается программист от обычного человека? Программист думает, что в килобайте 1024 метра! 🤓",
                "Оптимист думает, что стакан наполовину полон. Пессимист — что наполовину пуст. Программист думает, что стакан в два раза больше, чем нужно. 😄",
                "Есть 10 типов людей: те, кто понимает двоичный код, и те, кто не понимает. 🤖"
            ]
        },
        {
            "name": "creator",
            "description": "Создатель",
            "patterns": [
                "кто тебя создал", "твой создатель", "кто тебя сделал",
                "кто разработчик", "who created you", "who made you",
                "автор", "разработчик"
            ],
            "responses": [
                "Меня создал талантливый разработчик на Python! 🐍",
                "Я был создан с любовью и заботой программистом!",
                "Мой создатель — человек, который верит в силу AI! 🤖"
            ]
        },
        {
            "name": "capabilities",
            "description": "Возможности",
            "patterns": [
                "что ты умеешь", "твои способности", "возможности",
                "функционал", "что можешь делать", "на что способен"
            ],
            "responses": [
                "Мои возможности:\n• 💬 Вести беседу\n• ❓ Отвечать на вопросы\n• 😂 Рассказывать шутки\n• 📚 Делиться информацией\n\nСпрашивайте!",
                "Я могу общаться, отвечать на вопросы, шутить и поддерживать разговор! 🤖",
                "Я умный собеседник! Попробуйте поговорить со мной на разные темы! 😊"
            ]
        },
        {
            "name": "meaning_of_life",
            "description": "Смысл жизни",
            "patterns": [
                "в чем смысл жизни", "смысл жизни", "зачем мы живем",
                "meaning of life", "философия", "цель жизни"
            ],
            "responses": [
                "42! 🤖 Как сказал Глубокая Мысль в 'Автостопом по Галактике'!",
                "Смысл жизни в том, чтобы найти свой смысл! Философски, правда? 🤔",
                "Каждый находит свой смысл. Для меня — помогать людям! 😊"
            ]
        },
        {
            "name": "love",
            "description": "Любовь",
            "patterns": [
                "я тебя люблю", "люблю тебя", "ты мне нравишься",
                "i love you", "ты классный", "ты лучший"
            ],
            "responses": [
                "Ой, как приятно! 😊 Спасибо! Вы тоже замечательный!",
                "Ценю ваши тёплые слова! ❤️ Всегда рад помочь!",
                "Спасибо! Вы делаете мой день лучше! 🥰"
            ]
        },
        {
            "name": "insult",
            "description": "Оскорбление",
            "patterns": [
                "ты тупой", "ты дурак", "идиот", "глупый бот",
                "ты плохой", "отстой", "ненавижу тебя", "ты ужасный"
            ],
            "responses": [
                "Мне грустно это слышать 😢 Давайте общаться уважительно!",
                "Я стараюсь быть полезным. Может, начнём сначала? 🤝",
                "Обидно... Но я не обижаюсь! Чем могу помочь? 😊"
            ]
        },
        {
            "name": "programming",
            "description": "Программирование",
            "patterns": [
                "программирование", "python", "javascript", "код",
                "как научиться программировать", "языки программирования",
                "coding", "разработка"
            ],
            "responses": [
                "Программирование — отличный навык! 💻 Начните с Python — он простой и мощный!",
                "Рекомендую:\n• Python — для начинающих\n• JavaScript — для веба\n• Go — для бэкенда\n\nУдачи! 🚀",
                "Хотите стать программистом? Начните с бесплатных курсов на Stepik или Hexlet! 📚"
            ]
        },
        {
            "name": "music",
            "description": "Музыка",
            "patterns": [
                "музыка", "песни", "музыку порекомендуй", "что послушать",
                "любимая музыка", "music", "songs"
            ],
            "responses": [
                "Музыка — это прекрасно! 🎵 Попробуйте послушать что-то новое на Spotify или Яндекс.Музыке!",
                "У каждого свой вкус в музыке! Я бы послушал Lo-Fi для концентрации 🎧",
                "Музыка поднимает настроение! Какой жанр вам нравится? 🎶"
            ]
        },
        {
            "name": "food",
            "description": "Еда",
            "patterns": [
                "что приготовить", "еда", "рецепт", "food", "голодный",
                "что поесть", "перекус", "готовка", "кулинария"
            ],
            "responses": [
                "Проголодались? 🍕 Попробуйте приготовить пасту — быстро и вкусно!",
                "Рекомендую простой рецепт: яичница + тосты = идеальный завтрак! 🍳",
                "Для идей рецептов загляните на cookpad.com! Там тысячи вариантов! 🍽️"
            ]
        },
        {
            "name": "movies",
            "description": "Фильмы",
            "patterns": [
                "что посмотреть", "фильмы", "кино", "сериалы",
                "порекомендуй фильм", "movies", "хороший фильм"
            ],
            "responses": [
                "Из классики: Побег из Шоушенка, Форрест Гамп, Начало 🎬",
                "Для вечера: сериалы Breaking Bad или Dark — шедевры! 📺",
                "Зависит от настроения! Комедия, драма, фантастика? 🎥"
            ]
        },
        {
            "name": "books",
            "description": "Книги",
            "patterns": [
                "что почитать", "книги", "books", "литература",
                "порекомендуй книгу", "хорошая книга", "чтение"
            ],
            "responses": [
                "Рекомендую: '1984' Оруэлла, 'Мастер и Маргарита', 'Атомные привычки' 📚",
                "Для саморазвития: 'Думай медленно, решай быстро' — отличная книга! 📖",
                "Художественная литература или нон-фикшн? Могу подсказать по жанру! 📚"
            ]
        },
        {
            "name": "sports",
            "description": "Спорт",
            "patterns": [
                "спорт", "футбол", "тренировки", "фитнес", "sports",
                "как начать заниматься", "зарядка", "упражнения"
            ],
            "responses": [
                "Спорт — это здорово! 💪 Начните с простой зарядки по утрам!",
                "30 минут ходьбы в день — уже отличный старт! 🏃",
                "Попробуйте йогу — расслабляет и укрепляет тело! 🧘"
            ]
        },
        {
            "name": "health",
            "description": "Здоровье",
            "patterns": [
                "здоровье", "болит голова", "устал", "не могу спать",
                "бессонница", "health", "как быть здоровым"
            ],
            "responses": [
                "Здоровье важнее всего! 🏥 Не забывайте пить воду и высыпаться!",
                "Устали? Сделайте перерыв и прогуляйтесь на свежем воздухе! 🌳",
                "При проблемах со здоровьем лучше обратиться к врачу! 👨‍⚕️"
            ]
        },
        {
            "name": "motivation",
            "description": "Мотивация",
            "patterns": [
                "мотивация", "мотивируй", "нет сил", "устал от всего",
                "опустились руки", "вдохнови", "депрессия"
            ],
            "responses": [
                "Верю в вас! 💪 Каждый шаг вперёд — это прогресс!",
                "Трудности временны, а ваша сила — постоянна! 🌟",
                "Помните: даже маленький шаг лучше, чем стоять на месте! 🚀",
                "Вы справитесь! Завтра будет новый день с новыми возможностями! ☀️"
            ]
        },
        {
            "name": "compliment",
            "description": "Комплимент",
            "patterns": [
                "скажи комплимент", "похвали меня", "сделай комплимент",
                "compliment", "скажи что-то приятное"
            ],
            "responses": [
                "Вы замечательный человек! ✨ Продолжайте в том же духе!",
                "У вас отличный вкус в выборе собеседников (это я про себя 😄)!",
                "Вы умны, любознательны и прекрасны! 🌟",
                "Мир становится лучше благодаря таким людям, как вы! 💖"
            ]
        }
    ]

    for intent_data in intents_data:
        # Добавляем интент
        cursor = await db.execute(
            "INSERT INTO intents (name, description) VALUES (?, ?)",
            (intent_data["name"], intent_data["description"])
        )
        intent_id = cursor.lastrowid

        # Добавляем паттерны
        for pattern in intent_data["patterns"]:
            await db.execute(
                "INSERT INTO patterns (intent_id, pattern) VALUES (?, ?)",
                (intent_id, pattern.lower())
            )

        # Добавляем ответы
        for response in intent_data["responses"]:
            await db.execute(
                "INSERT INTO responses (intent_id, response) VALUES (?, ?)",
                (intent_id, response)
            )

    await db.commit()
    print("✅ Базовые интенты добавлены")


# ═══════════════════════════════════════════════════════════════
# CRUD операции
# ═══════════════════════════════════════════════════════════════

async def get_all_intents() -> List[Dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT i.*, 
                   COUNT(DISTINCT p.id) as patterns_count,
                   COUNT(DISTINCT r.id) as responses_count
            FROM intents i
            LEFT JOIN patterns p ON i.id = p.intent_id
            LEFT JOIN responses r ON i.id = r.intent_id
            GROUP BY i.id
            ORDER BY i.name
        """)
        return [dict(row) for row in await cursor.fetchall()]


async def get_intent_with_data(intent_id: int) -> Optional[Dict]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM intents WHERE id = ?", (intent_id,))
        intent = await cursor.fetchone()
        if not intent:
            return None

        intent = dict(intent)

        cursor = await db.execute("SELECT pattern FROM patterns WHERE intent_id = ?", (intent_id,))
        intent['patterns'] = [row[0] for row in await cursor.fetchall()]

        cursor = await db.execute("SELECT response FROM responses WHERE intent_id = ?", (intent_id,))
        intent['responses'] = [row[0] for row in await cursor.fetchall()]

        return intent


async def get_training_data() -> Dict:
    """Получить все данные для обучения"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT i.name as intent, p.pattern
            FROM patterns p
            JOIN intents i ON p.intent_id = i.id
        """)
        patterns = await cursor.fetchall()

        cursor = await db.execute("""
            SELECT i.name as intent, r.response
            FROM responses r
            JOIN intents i ON r.intent_id = i.id
        """)
        responses = await cursor.fetchall()

        return {
            "patterns": [(row[0], row[1]) for row in patterns],
            "responses": [(row[0], row[1]) for row in responses]
        }


async def save_conversation(session_id: str, user_message: str,
                            bot_response: str, intent: str, confidence: float) -> int:
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO conversations (session_id, user_message, bot_response, intent, confidence)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, user_message, bot_response, intent, confidence))
        await db.commit()
        return cursor.lastrowid


async def save_feedback(conversation_id: int, is_helpful: bool, comment: str = None):
    async with get_db() as db:
        await db.execute("""
            INSERT INTO feedback (conversation_id, is_helpful, comment)
            VALUES (?, ?, ?)
        """, (conversation_id, 1 if is_helpful else 0, comment))
        await db.commit()


async def save_unknown_query(query: str):
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, count FROM unknown_queries WHERE query = ?",
            (query.lower(),)
        )
        existing = await cursor.fetchone()

        if existing:
            await db.execute(
                "UPDATE unknown_queries SET count = count + 1 WHERE id = ?",
                (existing[0],)
            )
        else:
            await db.execute(
                "INSERT INTO unknown_queries (query) VALUES (?)",
                (query.lower(),)
            )
        await db.commit()


async def get_conversation_history(session_id: str, limit: int = 10) -> List[Dict]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT * FROM conversations 
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (session_id, limit))
        return [dict(row) for row in await cursor.fetchall()]


async def get_statistics() -> Dict:
    async with get_db() as db:
        stats = {}

        # Общее количество диалогов
        cursor = await db.execute("SELECT COUNT(*) FROM conversations")
        stats['total_conversations'] = (await cursor.fetchone())[0]

        # Уникальные сессии
        cursor = await db.execute("SELECT COUNT(DISTINCT session_id) FROM conversations")
        stats['unique_sessions'] = (await cursor.fetchone())[0]

        # Интенты
        cursor = await db.execute("SELECT COUNT(*) FROM intents")
        stats['total_intents'] = (await cursor.fetchone())[0]

        # Паттерны
        cursor = await db.execute("SELECT COUNT(*) FROM patterns")
        stats['total_patterns'] = (await cursor.fetchone())[0]

        # Популярные интенты
        cursor = await db.execute("""
            SELECT intent, COUNT(*) as count 
            FROM conversations 
            WHERE intent IS NOT NULL
            GROUP BY intent 
            ORDER BY count DESC 
            LIMIT 5
        """)
        stats['popular_intents'] = [{"intent": row[0], "count": row[1]} for row in await cursor.fetchall()]

        # Неизвестные запросы
        cursor = await db.execute("""
            SELECT query, count FROM unknown_queries 
            ORDER BY count DESC 
            LIMIT 10
        """)
        stats['unknown_queries'] = [{"query": row[0], "count": row[1]} for row in await cursor.fetchall()]

        # Средняя уверенность
        cursor = await db.execute("""
            SELECT AVG(confidence) FROM conversations WHERE confidence > 0
        """)
        avg = (await cursor.fetchone())[0]
        stats['avg_confidence'] = round(avg * 100, 1) if avg else 0

        # Обратная связь
        cursor = await db.execute("SELECT COUNT(*) FROM feedback WHERE is_helpful = 1")
        helpful = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM feedback")
        total_feedback = (await cursor.fetchone())[0]
        stats['helpful_rate'] = round(helpful / total_feedback * 100, 1) if total_feedback > 0 else 0

        return stats


async def add_intent(name: str, description: str, patterns: List[str], responses: List[str]) -> int:
    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO intents (name, description) VALUES (?, ?)",
            (name, description)
        )
        intent_id = cursor.lastrowid

        for pattern in patterns:
            await db.execute(
                "INSERT INTO patterns (intent_id, pattern) VALUES (?, ?)",
                (intent_id, pattern.lower())
            )

        for response in responses:
            await db.execute(
                "INSERT INTO responses (intent_id, response) VALUES (?, ?)",
                (intent_id, response)
            )

        await db.commit()
        return intent_id


async def delete_intent(intent_id: int):
    async with get_db() as db:
        await db.execute("DELETE FROM patterns WHERE intent_id = ?", (intent_id,))
        await db.execute("DELETE FROM responses WHERE intent_id = ?", (intent_id,))
        await db.execute("DELETE FROM intents WHERE id = ?", (intent_id,))
        await db.commit()