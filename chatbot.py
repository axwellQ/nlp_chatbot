"""
NLP движок чат-бота
"""

import re
import random
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.stem import SnowballStemmer
from nltk.tokenize import word_tokenize

# Загружаем необходимые ресурсы NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)


class NLPChatBot:
    def __init__(self):
        self.stemmer = SnowballStemmer("russian")
        self.vectorizer = TfidfVectorizer(tokenizer=self._tokenize, lowercase=True)
        self.patterns: List[str] = []
        self.intents: List[str] = []
        self.responses: Dict[str, List[str]] = {}
        self.is_trained = False
        self.tfidf_matrix = None
        self.confidence_threshold = 0.3

        # Синонимы для расширения понимания
        self.synonyms = {
            "привет": ["хай", "хеллоу", "здравствуй", "здорово", "салют"],
            "пока": ["до свидания", "бай", "прощай", "увидимся"],
            "спасибо": ["благодарю", "спс", "пасиб", "мерси"],
            "хорошо": ["отлично", "супер", "замечательно", "прекрасно"],
            "плохо": ["ужасно", "отстой", "кошмар", "беда"],
        }

    def _tokenize(self, text: str) -> List[str]:
        """Токенизация и стемминг текста"""
        # Очистка текста
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # Токенизация
        try:
            tokens = word_tokenize(text, language='russian')
        except:
            tokens = text.split()

        # Стемминг
        stemmed = [self.stemmer.stem(token) for token in tokens if len(token) > 1]

        return stemmed

    def train(self, patterns: List[Tuple[str, str]], responses: Dict[str, List[str]]):
        """Обучение модели"""
        self.patterns = []
        self.intents = []
        self.responses = responses

        for intent, pattern in patterns:
            self.patterns.append(pattern)
            self.intents.append(intent)

        if self.patterns:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.patterns)
            self.is_trained = True
            print(f"✅ Модель обучена на {len(self.patterns)} паттернах")
        else:
            print("⚠️ Нет данных для обучения")

    def _expand_with_synonyms(self, text: str) -> str:
        """Расширение текста синонимами"""
        words = text.lower().split()
        expanded = words.copy()

        for word in words:
            for base, syns in self.synonyms.items():
                if word == base or word in syns:
                    expanded.extend(syns)
                    expanded.append(base)

        return ' '.join(set(expanded))

    def predict(self, text: str) -> Tuple[str, float]:
        """Предсказание интента"""
        if not self.is_trained:
            return "unknown", 0.0

        # Преобразуем входной текст
        text_vector = self.vectorizer.transform([text])

        # Вычисляем косинусное сходство
        similarities = cosine_similarity(text_vector, self.tfidf_matrix).flatten()

        # Находим лучшее совпадение
        best_idx = np.argmax(similarities)
        confidence = similarities[best_idx]

        if confidence < self.confidence_threshold:
            return "unknown", confidence

        return self.intents[best_idx], confidence

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