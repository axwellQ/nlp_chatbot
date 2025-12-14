
import re
import random
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Безопасная загрузка NLTK
import nltk
import ssl

# Отключаем проверку SSL для загрузки
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Загружаем необходимые ресурсы NLTK
def download_nltk_data():
    """Безопасная загрузка NLTK данных"""
    resources = ['punkt', 'stopwords']
    for resource in resources:
        try:
            nltk.data.find(f'tokenizers/{resource}')
        except LookupError:
            try:
                nltk.download(resource, quiet=True)
            except Exception as e:
                print(f"Предупреждение: не удалось загрузить {resource}: {e}")

# Пытаемся загрузить при импорте
try:
    download_nltk_data()
except Exception as e:
    print(f"Предупреждение NLTK: {e}")


class NLPChatBot:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            tokenizer=self._tokenize,
            lowercase=True,
            token_pattern=None  # Отключаем встроенный токенизатор
        )
        self.patterns: List[str] = []
        self.intents: List[str] = []
        self.responses: Dict[str, List[str]] = {}
        self.is_trained = False
        self.tfidf_matrix = None
        self.confidence_threshold = 0.3

        # Русские стоп-слова
        self.stop_words = {
            'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как',
            'а', 'то', 'все', 'она', 'так', 'его', 'но', 'да', 'ты', 'к',
            'у', 'же', 'вы', 'за', 'бы', 'по', 'только', 'её', 'мне', 'было',
            'вот', 'от', 'меня', 'ещё', 'нет', 'о', 'из', 'ему', 'теперь',
            'когда', 'уже', 'для', 'вот', 'кто', 'этот', 'того', 'потому',
            'этого', 'какой', 'совсем', 'ним', 'здесь', 'этом', 'один',
            'почти', 'мой', 'тем', 'чтобы', 'нее', 'сейчас', 'были', 'куда',
            'зачем', 'всех', 'никогда', 'можно', 'при', 'наконец', 'два',
            'об', 'другой', 'хоть', 'после', 'над', 'больше', 'тот', 'через',
            'эти', 'нас', 'про', 'всего', 'них', 'какая', 'много', 'разве',
            'три', 'эту', 'моя', 'впрочем', 'хорошо', 'свою', 'этой', 'перед',
            'иногда', 'лучше', 'чуть', 'том', 'нельзя', 'такой', 'им', 'более',
            'всегда', 'конечно', 'всю', 'между', 'the', 'a', 'an', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'must', 'shall', 'can', 'need', 'dare', 'ought', 'used', 'to'
        }

        # Простые окончания для стемминга
        self.endings = ['ами', 'ями', 'ах', 'ях', 'ой', 'ей', 'ом', 'ем',
                       'ого', 'его', 'ому', 'ему', 'ых', 'их', 'ую', 'юю',
                       'ая', 'яя', 'ое', 'ее', 'ие', 'ые', 'ий', 'ый', 'ой',
                       'ов', 'ев', 'ам', 'ям', 'ть', 'ешь', 'ет', 'ем', 'ете',
                       'ут', 'ют', 'ишь', 'ит', 'им', 'ите', 'ат', 'ят']

    def _simple_stem(self, word: str) -> str:
        """Простой стемминг без NLTK"""
        word = word.lower()
        if len(word) <= 3:
            return word

        for ending in sorted(self.endings, key=len, reverse=True):
            if word.endswith(ending) and len(word) - len(ending) >= 2:
                return word[:-len(ending)]

        return word

    def _tokenize(self, text: str) -> List[str]:
        """Токенизация и стемминг текста"""
        # Очистка текста
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # Простая токенизация по пробелам
        tokens = text.split()

        # Фильтрация и стемминг
        result = []
        for token in tokens:
            if len(token) > 1 and token not in self.stop_words:
                stemmed = self._simple_stem(token)
                if len(stemmed) > 1:
                    result.append(stemmed)

        return result if result else ['_empty_']

    def train(self, patterns: List[Tuple[str, str]], responses: Dict[str, List[str]]):
        """Обучение модели"""
        self.patterns = []
        self.intents = []
        self.responses = responses

        for intent, pattern in patterns:
            self.patterns.append(pattern)
            self.intents.append(intent)

        if self.patterns:
            try:
                self.tfidf_matrix = self.vectorizer.fit_transform(self.patterns)
                self.is_trained = True
                print(f"✅ Модель обучена на {len(self.patterns)} паттернах")
            except Exception as e:
                print(f"❌ Ошибка обучения: {e}")
                self.is_trained = False
        else:
            print("⚠️ Нет данных для обучения")

    def predict(self, text: str) -> Tuple[str, float]:
        """Предсказание интента"""
        if not self.is_trained:
            return "unknown", 0.0

        try:
            # Преобразуем входной текст
            text_vector = self.vectorizer.transform([text])

            # Вычисляем косинусное сходство
            similarities = cosine_similarity(text_vector, self.tfidf_matrix).flatten()

            # Находим лучшее совпадение
            best_idx = np.argmax(similarities)
            confidence = float(similarities[best_idx])

            if confidence < self.confidence_threshold:
                return "unknown", confidence

            return self.intents[best_idx], confidence
        except Exception as e:
            print(f"Ошибка предсказания: {e}")
            return "unknown", 0.0

    def get_response(self, intent: str) -> str:
        """Получить случайный ответ для интента"""
        if intent in self.responses and self.responses[intent]:
            return random.choice(self.responses[intent])
        return self._get_fallback_response()

    def _get_fallback_response(self) -> str:
        """Ответ по умолчанию"""
        fallbacks = [
            "Извините, я не совсем понял. Можете перефразировать? 🤔",
            "Хм, интересный вопрос! Но я пока не знаю, как на него ответить.",
            "Я всё ещё учусь! Попробуйте спросить что-то другое. 📚",
            "Не уверен, что понял вас правильно. Можете уточнить?",
            "Это сложный вопрос для меня. Давайте поговорим о чём-то другом? 😊"
        ]
        return random.choice(fallbacks)

    def chat(self, user_input: str) -> Dict:
        """Основной метод чата"""
        # Предобработка
        user_input = user_input.strip()

        if not user_input:
            return {
                "response": "Вы ничего не написали. Напишите что-нибудь! 😊",
                "intent": None,
                "confidence": 0
            }

        # Предсказание интента
        intent, confidence = self.predict(user_input)

        # Получение ответа
        response = self.get_response(intent)

        return {
            "response": response,
            "intent": intent if intent != "unknown" else None,
            "confidence": round(confidence, 4)
        }


# Глобальный экземпляр бота
chatbot = NLPChatBot()


async def initialize_chatbot():
    """Инициализация и обучение чат-бота"""
    from database import get_training_data

    data = await get_training_data()

    # Формируем словарь ответов
    responses = {}
    for intent, response in data["responses"]:
        if intent not in responses:
            responses[intent] = []
        responses[intent].append(response)

    # Обучаем
    chatbot.train(data["patterns"], responses)

    return chatbot


def get_chatbot() -> NLPChatBot:
    """Получить экземпляр чат-бота"""
    return chatbot