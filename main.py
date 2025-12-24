from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from typing import Optional
import uvicorn
import uuid
from datetime import datetime

from database import (
    init_database, save_conversation, save_feedback,
    save_unknown_query, get_conversation_history,
    get_statistics, get_all_intents, add_intent,
    delete_intent, get_intent_with_data
)
from chatbot import initialize_chatbot, get_chatbot

app = FastAPI(title="🤖 NLP Chatbot")
app.add_middleware(SessionMiddleware, secret_key="chatbot-secret-key-2024")


# ═══════════════════════════════════════════════════════════════
# ИНИЦИАЛИЗАЦИЯ
# ═══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup():
    await init_database()
    await initialize_chatbot()
    print("🤖 Чат-бот готов к работе!")


def get_session_id(request: Request) -> str:
    """Получить или создать ID сессии"""
    if "session_id" not in request.session:
        request.session["session_id"] = str(uuid.uuid4())
    return request.session["session_id"]


# ═══════════════════════════════════════════════════════════════
# HTML ШАБЛОН
# ═══════════════════════════════════════════════════════════════

def base_template(content: str, title: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | NLP Chatbot</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        :root {{
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --dark: #1e293b;
            --gray: #64748b;
            --light: #f1f5f9;
            --white: #ffffff;
            --shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1);
            --radius: 16px;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: var(--dark);
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* Header */
        .header {{
            text-align: center;
            padding: 30px 0;
            color: white;
        }}

        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }}

        .header p {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}

        .nav {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 20px;
        }}

        .nav a {{
            padding: 10px 24px;
            background: rgba(255,255,255,0.2);
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-weight: 500;
            transition: all 0.3s;
        }}

        .nav a:hover, .nav a.active {{
            background: white;
            color: var(--primary);
        }}

        /* Chat Container */
        .chat-container {{
            max-width: 800px;
            margin: 0 auto;
            background: var(--white);
            border-radius: var(--radius);
            box-shadow: var(--shadow-lg);
            overflow: hidden;
        }}

        .chat-header {{
            background: var(--primary);
            color: white;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        .bot-avatar {{
            width: 50px;
            height: 50px;
            background: rgba(255,255,255,0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }}

        .bot-info h3 {{
            font-size: 1.2rem;
            margin-bottom: 4px;
        }}

        .bot-status {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85rem;
            opacity: 0.9;
        }}

        .status-dot {{
            width: 8px;
            height: 8px;
            background: #4ade80;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}

        .chat-messages {{
            height: 500px;
            overflow-y: auto;
            padding: 20px;
            background: #f8fafc;
        }}

        .message {{
            display: flex;
            margin-bottom: 16px;
            animation: fadeIn 0.3s ease;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .message.user {{
            justify-content: flex-end;
        }}

        .message-content {{
            max-width: 70%;
            padding: 12px 18px;
            border-radius: var(--radius);
            position: relative;
        }}

        .message.bot .message-content {{
            background: white;
            box-shadow: var(--shadow);
            border-bottom-left-radius: 4px;
        }}

        .message.user .message-content {{
            background: var(--primary);
            color: white;
            border-bottom-right-radius: 4px;
        }}

        .message-time {{
            font-size: 0.75rem;
            color: var(--gray);
            margin-top: 6px;
        }}

        .message.user .message-time {{
            color: rgba(255,255,255,0.7);
            text-align: right;
        }}

        .message-meta {{
            font-size: 0.75rem;
            color: var(--gray);
            margin-top: 4px;
            display: flex;
            gap: 10px;
        }}

        .confidence {{
            background: var(--light);
            padding: 2px 8px;
            border-radius: 10px;
        }}

        .confidence.high {{ background: #d1fae5; color: #065f46; }}
        .confidence.medium {{ background: #fef3c7; color: #92400e; }}
        .confidence.low {{ background: #fee2e2; color: #991b1b; }}

        /* Chat Input */
        .chat-input {{
            padding: 20px;
            background: white;
            border-top: 1px solid var(--light);
        }}

        .input-form {{
            display: flex;
            gap: 12px;
        }}

        .input-form input {{
            flex: 1;
            padding: 14px 20px;
            border: 2px solid var(--light);
            border-radius: 50px;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.3s;
        }}

        .input-form input:focus {{
            border-color: var(--primary);
        }}

        .input-form button {{
            padding: 14px 28px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
        }}

        .input-form button:hover {{
            background: var(--primary-dark);
        }}

        /* Quick Actions */
        .quick-actions {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 0 20px 20px;
            background: white;
        }}

        .quick-btn {{
            padding: 8px 16px;
            background: var(--light);
            border: none;
            border-radius: 50px;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.3s;
        }}

        .quick-btn:hover {{
            background: var(--primary);
            color: white;
        }}

        /* Feedback */
        .feedback-btns {{
            display: flex;
            gap: 8px;
            margin-top: 8px;
        }}

        .feedback-btn {{
            padding: 4px 12px;
            border: 1px solid var(--light);
            background: white;
            border-radius: 20px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.3s;
        }}

        .feedback-btn:hover {{
            border-color: var(--primary);
            color: var(--primary);
        }}

        .feedback-btn.positive:hover {{
            background: #d1fae5;
            border-color: #10b981;
            color: #065f46;
        }}

        .feedback-btn.negative:hover {{
            background: #fee2e2;
            border-color: #ef4444;
            color: #991b1b;
        }}

        /* Cards */
        .card {{
            background: white;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            overflow: hidden;
            margin-bottom: 20px;
        }}

        .card-header {{
            padding: 20px;
            border-bottom: 1px solid var(--light);
            font-weight: 600;
            font-size: 1.1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .card-body {{
            padding: 20px;
        }}

        /* Stats */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            padding: 24px;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            text-align: center;
        }}

        .stat-card .icon {{
            font-size: 40px;
            margin-bottom: 12px;
        }}

        .stat-card .value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary);
        }}

        .stat-card .label {{
            color: var(--gray);
            font-size: 0.9rem;
            margin-top: 4px;
        }}

        /* Table */
        .table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .table th, .table td {{
            padding: 14px;
            text-align: left;
            border-bottom: 1px solid var(--light);
        }}

        .table th {{
            font-weight: 600;
            color: var(--gray);
            font-size: 0.85rem;
            text-transform: uppercase;
        }}

        .table tr:hover {{
            background: var(--light);
        }}

        /* Buttons */
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            border-radius: var(--radius);
            font-weight: 500;
            font-size: 0.9rem;
            cursor: pointer;
            border: none;
            text-decoration: none;
            transition: all 0.3s;
        }}

        .btn-primary {{
            background: var(--primary);
            color: white;
        }}

        .btn-primary:hover {{
            background: var(--primary-dark);
        }}

        .btn-danger {{
            background: var(--danger);
            color: white;
        }}

        .btn-sm {{
            padding: 6px 12px;
            font-size: 0.8rem;
        }}

        /* Forms */
        .form-group {{
            margin-bottom: 20px;
        }}

        .form-label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }}

        .form-control {{
            width: 100%;
            padding: 12px 16px;
            border: 2px solid var(--light);
            border-radius: var(--radius);
            font-size: 1rem;
        }}

        .form-control:focus {{
            outline: none;
            border-color: var(--primary);
        }}

        textarea.form-control {{
            min-height: 100px;
            resize: vertical;
        }}

        /* Badge */
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .badge-primary {{ background: #e0e7ff; color: #4338ca; }}
        .badge-success {{ background: #d1fae5; color: #065f46; }}
        .badge-warning {{ background: #fef3c7; color: #92400e; }}

        /* Typing indicator */
        .typing {{
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 12px 18px;
            background: white;
            border-radius: var(--radius);
            width: fit-content;
            box-shadow: var(--shadow);
        }}

        .typing span {{
            width: 8px;
            height: 8px;
            background: var(--gray);
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }}

        .typing span:nth-child(2) {{ animation-delay: 0.2s; }}
        .typing span:nth-child(3) {{ animation-delay: 0.4s; }}

        @keyframes typing {{
            0%, 60%, 100% {{ transform: translateY(0); }}
            30% {{ transform: translateY(-10px); }}
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 1.8rem; }}
            .chat-messages {{ height: 400px; }}
            .message-content {{ max-width: 85%; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}

        /* Scrollbar */
        .chat-messages::-webkit-scrollbar {{
            width: 6px;
        }}

        .chat-messages::-webkit-scrollbar-track {{
            background: transparent;
        }}

        .chat-messages::-webkit-scrollbar-thumb {{
            background: var(--gray);
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🤖 NLP Chatbot</h1>
            <p>Умный чат-бот с обработкой естественного языка</p>
            <nav class="nav">
                <a href="/" class="{'active' if title == 'Чат' else ''}">💬 Чат</a>
                <a href="/stats" class="{'active' if title == 'Статистика' else ''}">📊 Статистика</a>
                <a href="/train" class="{'active' if title == 'Обучение' else ''}">🧠 Обучение</a>
            </nav>
        </header>

        {content}
    </div>

    <script>
        function scrollToBottom() {{
            const messages = document.getElementById('chat-messages');
            if (messages) {{
                messages.scrollTop = messages.scrollHeight;
            }}
        }}

        window.onload = scrollToBottom;
    </script>
</body>
</html>
"""


# ═══════════════════════════════════════════════════════════════
# ГЛАВНАЯ СТРАНИЦА - ЧАТ
# ═══════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    session_id = get_session_id(request)
    history = await get_conversation_history(session_id, 20)
    history = list(reversed(history))

    messages_html = ""
    for msg in history:
        confidence_class = "high" if msg['confidence'] and msg['confidence'] > 0.7 else (
            "medium" if msg['confidence'] and msg['confidence'] > 0.4 else "low")

        # Сообщение пользователя
        messages_html += f"""
        <div class="message user">
            <div class="message-content">
                {msg['user_message']}
                <div class="message-time">{msg['created_at'][11:16] if msg['created_at'] else ''}</div>
            </div>
        </div>
        """

        # Ответ бота
        messages_html += f"""
        <div class="message bot">
            <div class="message-content">
                {msg['bot_response']}
                <div class="message-meta">
                    <span>Интент: {msg['intent'] or 'unknown'}</span>
                    <span class="confidence {confidence_class}">
                        {int(msg['confidence'] * 100) if msg['confidence'] else 0}% уверенность
                    </span>
                </div>
                <div class="feedback-btns">
                    <button class="feedback-btn positive" onclick="sendFeedback({msg['id']}, true)">👍 Полезно</button>
                    <button class="feedback-btn negative" onclick="sendFeedback({msg['id']}, false)">👎 Нет</button>
                </div>
            </div>
        </div>
        """

    if not messages_html:
        messages_html = """
        <div style="text-align: center; padding: 40px; color: var(--gray);">
            <div style="font-size: 60px; margin-bottom: 20px;">👋</div>
            <h3 style="margin-bottom: 10px;">Привет! Я умный чат-бот</h3>
            <p>Напишите мне что-нибудь или выберите быстрое действие ниже</p>
        </div>
        """

    content = f"""
    <div class="chat-container">
        <div class="chat-header">
            <div class="bot-avatar">🤖</div>
            <div class="bot-info">
                <h3>ChatBot AI</h3>
                <div class="bot-status">
                    <span class="status-dot"></span>
                    Онлайн
                </div>
            </div>
        </div>

        <div class="chat-messages" id="chat-messages">
            {messages_html}
        </div>

        <div class="quick-actions">
            <button class="quick-btn" onclick="sendQuick('Привет!')">👋 Привет</button>
            <button class="quick-btn" onclick="sendQuick('Как дела?')">🙂 Как дела?</button>
            <button class="quick-btn" onclick="sendQuick('Р��сскажи шутку')">😂 Шутка</button>
            <button class="quick-btn" onclick="sendQuick('Что ты умеешь?')">🤔 Возможности</button>
            <button class="quick-btn" onclick="sendQuick('Мотивируй меня')">💪 Мотивация</button>
            <button class="quick-btn" onclick="sendQuick('Посоветуй книгу')">📚 Книга</button>
        </div>

        <div class="chat-input">
            <form class="input-form" id="chat-form" onsubmit="sendMessage(event)">
                <input type="text" id="user-input" placeholder="Напишите сообщение..." autocomplete="off">
                <button type="submit">Отправить</button>
            </form>
        </div>
    </div>

    <script>
        async function sendMessage(e) {{
            e.preventDefault();
            const input = document.getElementById('user-input');
            const message = input.value.trim();
            if (!message) return;

            input.value = '';

            // Добавляем сообщение пользователя
            addMessage(message, 'user');

            // Показываем индикатор печати
            showTyping();

            // Отправляем запрос
            const response = await fetch('/api/chat', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ message: message }})
            }});

            const data = await response.json();

            // Убираем индикатор печати
            hideTyping();

            // Добавляем ответ бота
            addBotMessage(data);
        }}

        function sendQuick(message) {{
            document.getElementById('user-input').value = message;
            document.getElementById('chat-form').dispatchEvent(new Event('submit'));
        }}

        function addMessage(text, type) {{
            const messages = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.className = 'message ' + type;
            div.innerHTML = `
                <div class="message-content">
                    ${{text}}
                    <div class="message-time">${{new Date().toLocaleTimeString('ru', {{hour: '2-digit', minute: '2-digit'}})}}</div>
                </div>
            `;
            messages.appendChild(div);
            scrollToBottom();
        }}

        function addBotMessage(data) {{
            const messages = document.getElementById('chat-messages');
            const confidenceClass = data.confidence > 0.7 ? 'high' : (data.confidence > 0.4 ? 'medium' : 'low');

            const div = document.createElement('div');
            div.className = 'message bot';
            div.innerHTML = `
                <div class="message-content">
                    ${{data.response}}
                    <div class="message-meta">
                        <span>Интент: ${{data.intent || 'unknown'}}</span>
                        <span class="confidence ${{confidenceClass}}">
                            ${{Math.round(data.confidence * 100)}}% уверенность
                        </span>
                    </div>
                    <div class="feedback-btns">
                        <button class="feedback-btn positive" onclick="sendFeedback(${{data.conversation_id}}, true)">👍 Полезно</button>
                        <button class="feedback-btn negative" onclick="sendFeedback(${{data.conversation_id}}, false)">👎 Нет</button>
                    </div>
                </div>
            `;
            messages.appendChild(div);
            scrollToBottom();
        }}

        function showTyping() {{
            const messages = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.className = 'message bot';
            div.id = 'typing-indicator';
            div.innerHTML = `
                <div class="typing">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            `;
            messages.appendChild(div);
            scrollToBottom();
        }}

        function hideTyping() {{
            const typing = document.getElementById('typing-indicator');
            if (typing) typing.remove();
        }}

        async function sendFeedback(conversationId, isHelpful) {{
            await fetch('/api/feedback', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ conversation_id: conversationId, is_helpful: isHelpful }})
            }});

            // Визуальная обратная связь
            event.target.style.background = isHelpful ? '#d1fae5' : '#fee2e2';
            event.target.style.borderColor = isHelpful ? '#10b981' : '#ef4444';
        }}

        function scrollToBottom() {{
            const messages = document.getElementById('chat-messages');
            messages.scrollTop = messages.scrollHeight;
        }}
    </script>
    """

    return HTMLResponse(base_template(content, "Чат"))


# ═══════════════════════════════════════════════════════════════
# API ЧАТ
# ═══════════════════════════════════════════════════════════════

@app.post("/api/chat")
async def api_chat(request: Request):
    session_id = get_session_id(request)
    data = await request.json()
    message = data.get("message", "").strip()

    if not message:
        return JSONResponse({"error": "Пустое сообщение"})

    # Получаем ответ от бота
    bot = get_chatbot()
    result = bot.chat(message)

    # Сохраняем диалог
    conversation_id = await save_conversation(
        session_id=session_id,
        user_message=message,
        bot_response=result["response"],
        intent=result["intent"],
        confidence=result["confidence"]
    )

    # Сохраняем неизвестные запросы
    if result["intent"] is None:
        await save_unknown_query(message)

    return JSONResponse({
        "response": result["response"],
        "intent": result["intent"],
        "confidence": result["confidence"],
        "conversation_id": conversation_id
    })


@app.post("/api/feedback")
async def api_feedback(request: Request):
    data = await request.json()
    conversation_id = data.get("conversation_id")
    is_helpful = data.get("is_helpful", True)
    comment = data.get("comment")

    if conversation_id:
        await save_feedback(conversation_id, is_helpful, comment)

    return JSONResponse({"success": True})


# ═══════════════════════════════════════════════════════════════
# СТАТИСТИКА
# ═══════════════════════════════════════════════════════════════

@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    stats = await get_statistics()

    # Популярные интенты
    popular_html = ""
    for item in stats['popular_intents']:
        popular_html += f"""
        <tr>
            <td><span class="badge badge-primary">{item['intent']}</span></td>
            <td>{item['count']}</td>
        </tr>
        """

    if not popular_html:
        popular_html = '<tr><td colspan="2" style="text-align: center; color: var(--gray);">Нет данных</td></tr>'

    # Неизвестные запросы
    unknown_html = ""
    for item in stats['unknown_queries']:
        unknown_html += f"""
        <tr>
            <td>{item['query']}</td>
            <td>{item['count']}</td>
            <td>
                <a href="/train?query={item['query']}" class="btn btn-primary btn-sm">+ Обучить</a>
            </td>
        </tr>
        """

    if not unknown_html:
        unknown_html = '<tr><td colspan="3" style="text-align: center; color: var(--gray);">Нет неизвестных запросов</td></tr>'

    content = f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="icon">💬</div>
            <div class="value">{stats['total_conversations']}</div>
            <div class="label">Всего сообщений</div>
        </div>
        <div class="stat-card">
            <div class="icon">👥</div>
            <div class="value">{stats['unique_sessions']}</div>
            <div class="label">Уникальных сессий</div>
        </div>
        <div class="stat-card">
            <div class="icon">🧠</div>
            <div class="value">{stats['total_intents']}</div>
            <div class="label">Интентов</div>
        </div>
        <div class="stat-card">
            <div class="icon">📝</div>
            <div class="value">{stats['total_patterns']}</div>
            <div class="label">Паттернов</div>
        </div>
        <div class="stat-card">
            <div class="icon">🎯</div>
            <div class="value">{stats['avg_confidence']}%</div>
            <div class="label">Средняя уверенность</div>
        </div>
        <div class="stat-card">
            <div class="icon">👍</div>
            <div class="value">{stats['helpful_rate']}%</div>
            <div class="label">Полезных ответов</div>
        </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="card">
            <div class="card-header">🏆 Популярные интенты</div>
            <div class="card-body">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Интент</th>
                            <th>Запросов</th>
                        </tr>
                    </thead>
                    <tbody>
                        {popular_html}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <div class="card-header">❓ Неизвестные запросы</div>
            <div class="card-body">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Запрос</th>
                            <th>Раз</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {unknown_html}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """

    return HTMLResponse(base_template(content, "Статистика"))


# ═══════════════════════════════════════════════════════════════
# ОБУЧЕНИЕ
# ═══════════════════════════════════════════════════════════════

@app.get("/train", response_class=HTMLResponse)
async def train_page(request: Request, query: str = ""):
    intents = await get_all_intents()

    intents_html = ""
    for intent in intents:
        intents_html += f"""
        <tr>
            <td><strong>{intent['name']}</strong></td>
            <td>{intent['description'] or '-'}</td>
            <td><span class="badge badge-success">{intent['patterns_count']}</span></td>
            <td><span class="badge badge-primary">{intent['responses_count']}</span></td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="deleteIntent({intent['id']})">🗑️</button>
            </td>
        </tr>
        """

    content = f"""
    <div class="card">
        <div class="card-header">
            ➕ Добавить новый интент
        </div>
        <div class="card-body">
            <form method="post" action="/train/add">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div class="form-group">
                        <label class="form-label">Название интента</label>
                        <input type="text" name="name" class="form-control" required 
                               placeholder="например: order_status">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Описание</label>
                        <input type="text" name="description" class="form-control" 
                               placeholder="например: Статус заказа">
                    </div>
                </div>

                <div class="form-group">
                    <label class="form-label">Паттерны (каждый с новой строки)</label>
                    <textarea name="patterns" class="form-control" required
                              placeholder="где мой заказ&#10;статус заказа&#10;когда доставка">{query}</textarea>
                </div>

                <div class="form-group">
                    <label class="form-label">Ответы (каждый с новой строки)</label>
                    <textarea name="responses" class="form-control" required
                              placeholder="Для проверки статуса заказа перейдите в личный кабинет!&#10;Отслеживайте заказ по номеру трека."></textarea>
                </div>

                <button type="submit" class="btn btn-primary">
                    ➕ Добавить интент
                </button>
            </form>
        </div>
    </div>

    <div class="card" style="margin-top: 20px;">
        <div class="card-header">
            📚 Существующие интенты ({len(intents)})
        </div>
        <div class="card-body">
            <table class="table">
                <thead>
                    <tr>
                        <th>Название</th>
                        <th>Описание</th>
                        <th>Паттерны</th>
                        <th>Ответы</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    {intents_html}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        async function deleteIntent(id) {{
            if (!confirm('Удалить этот интент?')) return;

            await fetch('/train/delete/' + id, {{ method: 'POST' }});
            location.reload();
        }}
    </script>
    """

    return HTMLResponse(base_template(content, "Обучение"))


@app.post("/train/add", response_class=HTMLResponse)
async def train_add(
        request: Request,
        name: str = Form(...),
        description: str = Form(""),
        patterns: str = Form(...),
        responses: str = Form(...)
):
    patterns_list = [p.strip() for p in patterns.split("\n") if p.strip()]
    responses_list = [r.strip() for r in responses.split("\n") if r.strip()]

    if patterns_list and responses_list:
        await add_intent(name, description, patterns_list, responses_list)
        # Переобучаем бота
        await initialize_chatbot()

    from fastapi.responses import RedirectResponse
    return RedirectResponse("/train", status_code=302)


@app.post("/train/delete/{intent_id}")
async def train_delete(intent_id: int):
    await delete_intent(intent_id)
    # Переобучаем бота
    await initialize_chatbot()
    return JSONResponse({"success": True})


# ═══════════════════════════════════════════════════════════════
# API ДЛЯ ИНТЕГРАЦИЙ
# ═══════════════════════════════════════════════════════════════

@app.get("/api/intents")
async def api_get_intents():
    """Получить все интенты"""
    intents = await get_all_intents()
    return JSONResponse({"intents": intents})


@app.get("/api/intents/{intent_id}")
async def api_get_intent(intent_id: int):
    """Получить интент с паттернами и ответами"""
    intent = await get_intent_with_data(intent_id)
    if not intent:
        return JSONResponse({"error": "Интент не найден"}, status_code=404)
    return JSONResponse({"intent": intent})


@app.post("/api/intents")
async def api_create_intent(request: Request):
    """Создать новый интент"""
    data = await request.json()

    name = data.get("name")
    description = data.get("description", "")
    patterns = data.get("patterns", [])
    responses = data.get("responses", [])

    if not name or not patterns or not responses:
        return JSONResponse({"error": "Необходимы name, patterns и responses"}, status_code=400)

    intent_id = await add_intent(name, description, patterns, responses)

    # Переобучаем бота
    await initialize_chatbot()

    return JSONResponse({"success": True, "intent_id": intent_id})


@app.delete("/api/intents/{intent_id}")
async def api_delete_intent(intent_id: int):
    """Удалить интент"""
    await delete_intent(intent_id)
    await initialize_chatbot()
    return JSONResponse({"success": True})


@app.get("/api/stats")
async def api_get_stats():
    """Получить статистику"""
    stats = await get_statistics()
    return JSONResponse(stats)


@app.post("/api/retrain")
async def api_retrain():
    """Переобучить модель"""
    await initialize_chatbot()
    return JSONResponse({"success": True, "message": "Модель переобучена"})


# ═══════════════════════════════════════════════════════════════
# ЭКСПОРТ/ИМПОРТ ДАННЫХ
# ═══════════════════════════════════════════════════════════════

@app.get("/api/export")
async def api_export():
    """Экспорт всех интентов в JSON"""
    intents = await get_all_intents()

    export_data = []
    for intent in intents:
        intent_data = await get_intent_with_data(intent['id'])
        if intent_data:
            export_data.append({
                "name": intent_data['name'],
                "description": intent_data['description'],
                "patterns": intent_data['patterns'],
                "responses": intent_data['responses']
            })

    return JSONResponse({
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "intents": export_data
    })


@app.post("/api/import")
async def api_import(request: Request):
    """Импорт интентов из JSON"""
    data = await request.json()
    intents = data.get("intents", [])

    imported = 0
    for intent_data in intents:
        try:
            await add_intent(
                name=intent_data['name'],
                description=intent_data.get('description', ''),
                patterns=intent_data['patterns'],
                responses=intent_data['responses']
            )
            imported += 1
        except Exception as e:
            print(f"Ошибка импорта {intent_data.get('name')}: {e}")

    # Переобучаем бота
    await initialize_chatbot()

    return JSONResponse({
        "success": True,
        "imported": imported,
        "total": len(intents)
    })


# ═══════════════════════════════════════════════════════════════
# СТРАНИЦА ЭКСПОРТА/ИМПОРТА
# ═══════════════════════════════════════════════════════════════

@app.get("/export", response_class=HTMLResponse)
async def export_page(request: Request):
    content = """
    <div class="card">
        <div class="card-header">📤 Экспорт данных</div>
        <div class="card-body">
            <p style="margin-bottom: 20px; color: var(--gray);">
                Экспортируйте все интенты, паттерны и ответы в JSON файл для резервного копирования или переноса.
            </p>
            <button class="btn btn-primary" onclick="exportData()">
                📥 Скачать JSON
            </button>
        </div>
    </div>

    <div class="card" style="margin-top: 20px;">
        <div class="card-header">📥 Импорт данных</div>
        <div class="card-body">
            <p style="margin-bottom: 20px; color: var(--gray);">
                Загрузите JSON файл с интентами для добавления в базу знаний бота.
            </p>
            <input type="file" id="import-file" accept=".json" style="margin-bottom: 16px;">
            <br>
            <button class="btn btn-primary" onclick="importData()">
                📤 Импортировать
            </button>
            <div id="import-result" style="margin-top: 16px;"></div>
        </div>
    </div>

    <div class="card" style="margin-top: 20px;">
        <div class="card-header">📋 Формат JSON</div>
        <div class="card-body">
            <pre style="background: var(--light); padding: 16px; border-radius: 8px; overflow-x: auto;">
{
  "intents": [
    {
      "name": "greeting",
      "description": "Приветствие",
      "patterns": ["привет", "здравствуй", "добрый день"],
      "responses": ["Привет! 👋", "Здравствуйте!"]
    }
  ]
}
            </pre>
        </div>
    </div>

    <script>
        async function exportData() {
            const response = await fetch('/api/export');
            const data = await response.json();

            const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = 'chatbot_intents_' + new Date().toISOString().slice(0,10) + '.json';
            a.click();

            URL.revokeObjectURL(url);
        }

        async function importData() {
            const fileInput = document.getElementById('import-file');
            const resultDiv = document.getElementById('import-result');

            if (!fileInput.files.length) {
                resultDiv.innerHTML = '<div style="color: var(--danger);">❌ Выберите файл</div>';
                return;
            }

            const file = fileInput.files[0];
            const text = await file.text();

            try {
                const data = JSON.parse(text);

                const response = await fetch('/api/import', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.success) {
                    resultDiv.innerHTML = `
                        <div style="color: var(--success);">
                            ✅ Импортировано ${result.imported} из ${result.total} интентов
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `<div style="color: var(--danger);">❌ ${result.error}</div>`;
                }
            } catch (e) {
                resultDiv.innerHTML = `<div style="color: var(--danger);">❌ Ошибка парсинга JSON: ${e.message}</div>`;
            }
        }
    </script>
    """

    return HTMLResponse(base_template(content, "Экспорт/Импорт"))


# ═══════════════════════════════════════════════════════════════
# ИСТОРИЯ ДИАЛОГОВ
# ═══════════════════════════════════════════════════════════════

@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    session_id = get_session_id(request)
    history = await get_conversation_history(session_id, 50)

    history_html = ""
    for msg in history:
        confidence_class = "high" if msg['confidence'] and msg['confidence'] > 0.7 else (
            "medium" if msg['confidence'] and msg['confidence'] > 0.4 else "low")

        history_html += f"""
        <tr>
            <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                {msg['user_message']}
            </td>
            <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                {msg['bot_response']}
            </td>
            <td><span class="badge badge-primary">{msg['intent'] or 'unknown'}</span></td>
            <td><span class="badge {'badge-success' if msg['confidence'] and msg['confidence'] > 0.7 else 'badge-warning'}">{int(msg['confidence'] * 100) if msg['confidence'] else 0}%</span></td>
            <td style="color: var(--gray); font-size: 0.85rem;">{msg['created_at'][:16] if msg['created_at'] else ''}</td>
        </tr>
        """

    if not history_html:
        history_html = '<tr><td colspan="5" style="text-align: center; color: var(--gray); padding: 40px;">История пуста. Начните диалог!</td></tr>'

    content = f"""
    <div class="card">
        <div class="card-header">
            📜 История диалогов
            <a href="/" class="btn btn-primary btn-sm">💬 К чату</a>
        </div>
        <div class="card-body">
            <table class="table">
                <thead>
                    <tr>
                        <th>Сообщение</th>
                        <th>Ответ</th>
                        <th>Интент</th>
                        <th>Уверенность</th>
                        <th>Время</th>
                    </tr>
                </thead>
                <tbody>
                    {history_html}
                </tbody>
            </table>
        </div>
    </div>
    """

    return HTMLResponse(base_template(content, "История"))


# ═══════════════════════════════════════════════════════════════
# ТЕСТИРОВАНИЕ БОТА
# ═══════════════════════════════════════════════════════════════

@app.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    content = """
    <div class="card">
        <div class="card-header">🧪 Тестирование бота</div>
        <div class="card-body">
            <p style="margin-bottom: 20px; color: var(--gray);">
                Введите несколько тестовых фраз и проверьте, как бот их распознаёт.
            </p>

            <div class="form-group">
                <label class="form-label">Тестовые фразы (каждая с новой строки)</label>
                <textarea id="test-phrases" class="form-control" rows="8" placeholder="привет
как дела
расскажи шутку
кто тебя создал
что ты умеешь"></textarea>
            </div>

            <button class="btn btn-primary" onclick="runTest()">
                🚀 Запустить тест
            </button>

            <div id="test-results" style="margin-top: 24px;"></div>
        </div>
    </div>

    <script>
        async function runTest() {
            const phrases = document.getElementById('test-phrases').value.split('\\n').filter(p => p.trim());
            const resultsDiv = document.getElementById('test-results');

            if (!phrases.length) {
                resultsDiv.innerHTML = '<div style="color: var(--danger);">Введите хотя бы одну фразу</div>';
                return;
            }

            resultsDiv.innerHTML = '<div style="color: var(--gray);">⏳ Тестирование...</div>';

            let html = '<table class="table"><thead><tr><th>Фраза</th><th>Интент</th><th>Уверенность</th><th>Ответ</th></tr></thead><tbody>';

            for (const phrase of phrases) {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: phrase})
                });
                const data = await response.json();

                const confidenceClass = data.confidence > 0.7 ? 'badge-success' : (data.confidence > 0.4 ? 'badge-warning' : 'badge-primary');

                html += `
                    <tr>
                        <td>${phrase}</td>
                        <td><span class="badge badge-primary">${data.intent || 'unknown'}</span></td>
                        <td><span class="badge ${confidenceClass}">${Math.round(data.confidence * 100)}%</span></td>
                        <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            ${data.response}
                        </td>
                    </tr>
                `;
            }

            html += '</tbody></table>';
            resultsDiv.innerHTML = html;
        }
    </script>
    """

    return HTMLResponse(base_template(content, "Тестирование"))


# ═══════════════════════════════════════════════════════════════
# ДОКУМЕНТАЦИЯ API
# ═══════════════════════════════════════════════════════════════

@app.get("/docs-custom", response_class=HTMLResponse)
async def docs_page(request: Request):
    content = """
    <div class="card">
        <div class="card-header">📚 API Документация</div>
        <div class="card-body">
            <h3 style="margin-bottom: 16px;">Основные эндпоинты</h3>

            <div style="background: var(--light); padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span class="badge badge-success">POST</span>
                    <code>/api/chat</code>
                </div>
                <p style="color: var(--gray); margin-bottom: 12px;">Отправить сообщение боту</p>
                <pre style="background: var(--dark); color: white; padding: 12px; border-radius: 8px; overflow-x: auto;">
// Запрос
{
  "message": "Привет, как дела?"
}

// Ответ
{
  "response": "Отлично! Спасибо, что спросили! 😊 А у вас?",
  "intent": "how_are_you",
  "confidence": 0.8542,
  "conversation_id": 123
}
                </pre>
            </div>

            <div style="background: var(--light); padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span class="badge badge-primary">GET</span>
                    <code>/api/intents</code>
                </div>
                <p style="color: var(--gray);">Получить список всех интентов</p>
            </div>

            <div style="background: var(--light); padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span class="badge badge-success">POST</span>
                    <code>/api/intents</code>
                </div>
                <p style="color: var(--gray); margin-bottom: 12px;">Создать новый интент</p>
                <pre style="background: var(--dark); color: white; padding: 12px; border-radius: 8px; overflow-x: auto;">
{
  "name": "order_status",
  "description": "Статус заказа",
  "patterns": ["где мой заказ", "статус заказа"],
  "responses": ["Проверьте статус в личном кабинете!"]
}
                </pre>
            </div>

            <div style="background: var(--light); padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span class="badge badge-danger">DELETE</span>
                    <code>/api/intents/{id}</code>
                </div>
                <p style="color: var(--gray);">Удалить интент</p>
            </div>

            <div style="background: var(--light); padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span class="badge badge-primary">GET</span>
                    <code>/api/stats</code>
                </div>
                <p style="color: var(--gray);">Получить статистику</p>
            </div>

            <div style="background: var(--light); padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span class="badge badge-primary">GET</span>
                    <code>/api/export</code>
                </div>
                <p style="color: var(--gray);">Экспортировать все интенты в JSON</p>
            </div>

            <div style="background: var(--light); padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span class="badge badge-success">POST</span>
                    <code>/api/import</code>
                </div>
                <p style="color: var(--gray);">Импортировать интенты из JSON</p>
            </div>

            <div style="background: var(--light); padding: 16px; border-radius: 8px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span class="badge badge-success">POST</span>
                    <code>/api/feedback</code>
                </div>
                <p style="color: var(--gray); margin-bottom: 12px;">Отправить обратную связь</p>
                <pre style="background: var(--dark); color: white; padding: 12px; border-radius: 8px; overflow-x: auto;">
{
  "conversation_id": 123,
  "is_helpful": true,
  "comment": "Отличный ответ!"
}
                </pre>
            </div>

            <h3 style="margin: 24px 0 16px;">Swagger UI</h3>
            <p style="color: var(--gray);">
                Автоматическая документация доступна по адресу: 
                <a href="/docs" target="_blank">/docs</a> (Swagger) или 
                <a href="/redoc" target="_blank">/redoc</a> (ReDoc)
            </p>
        </div>
    </div>
    """

    return HTMLResponse(base_template(content, "API Документация"))


# ═══════════════════════════════════════════════════════════════
# ОБНОВЛЕНИЕ НАВИГАЦИИ
# ═══════════════════════════════════════════════════════════════

def base_template(content: str, title: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | NLP Chatbot</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        :root {{
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --dark: #1e293b;
            --gray: #64748b;
            --light: #f1f5f9;
            --white: #ffffff;
            --shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1);
            --radius: 16px;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: var(--dark);
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        .header {{
            text-align: center;
            padding: 30px 0;
            color: white;
        }}

        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }}

        .header p {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}

        .nav {{
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}

        .nav a {{
            padding: 10px 20px;
            background: rgba(255,255,255,0.2);
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-weight: 500;
            font-size: 0.9rem;
            transition: all 0.3s;
        }}

        .nav a:hover, .nav a.active {{
            background: white;
            color: var(--primary);
        }}

        .chat-container {{
            max-width: 800px;
            margin: 0 auto;
            background: var(--white);
            border-radius: var(--radius);
            box-shadow: var(--shadow-lg);
            overflow: hidden;
        }}

        .chat-header {{
            background: var(--primary);
            color: white;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        .bot-avatar {{
            width: 50px;
            height: 50px;
            background: rgba(255,255,255,0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }}

        .bot-info h3 {{
            font-size: 1.2rem;
            margin-bottom: 4px;
        }}

        .bot-status {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85rem;
            opacity: 0.9;
        }}

        .status-dot {{
            width: 8px;
            height: 8px;
            background: #4ade80;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}

        .chat-messages {{
            height: 500px;
            overflow-y: auto;
            padding: 20px;
            background: #f8fafc;
        }}

        .message {{
            display: flex;
            margin-bottom: 16px;
            animation: fadeIn 0.3s ease;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .message.user {{
            justify-content: flex-end;
        }}

        .message-content {{
            max-width: 70%;
            padding: 12px 18px;
            border-radius: var(--radius);
            position: relative;
        }}

        .message.bot .message-content {{
            background: white;
            box-shadow: var(--shadow);
            border-bottom-left-radius: 4px;
        }}

        .message.user .message-content {{
            background: var(--primary);
            color: white;
            border-bottom-right-radius: 4px;
        }}

        .message-time {{
            font-size: 0.75rem;
            color: var(--gray);
            margin-top: 6px;
        }}

        .message.user .message-time {{
            color: rgba(255,255,255,0.7);
            text-align: right;
        }}

        .message-meta {{
            font-size: 0.75rem;
            color: var(--gray);
            margin-top: 4px;
            display: flex;
            gap: 10px;
        }}

        .confidence {{
            background: var(--light);
            padding: 2px 8px;
            border-radius: 10px;
        }}

        .confidence.high {{ background: #d1fae5; color: #065f46; }}
        .confidence.medium {{ background: #fef3c7; color: #92400e; }}
        .confidence.low {{ background: #fee2e2; color: #991b1b; }}

        .chat-input {{
            padding: 20px;
            background: white;
            border-top: 1px solid var(--light);
        }}

        .input-form {{
            display: flex;
            gap: 12px;
        }}

        .input-form input {{
            flex: 1;
            padding: 14px 20px;
            border: 2px solid var(--light);
            border-radius: 50px;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.3s;
        }}

        .input-form input:focus {{
            border-color: var(--primary);
        }}

        .input-form button {{
            padding: 14px 28px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
        }}

        .input-form button:hover {{
            background: var(--primary-dark);
        }}

        .quick-actions {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 0 20px 20px;
            background: white;
        }}

        .quick-btn {{
            padding: 8px 16px;
            background: var(--light);
            border: none;
            border-radius: 50px;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.3s;
        }}

        .quick-btn:hover {{
            background: var(--primary);
            color: white;
        }}

        .feedback-btns {{
            display: flex;
            gap: 8px;
            margin-top: 8px;
        }}

        .feedback-btn {{
            padding: 4px 12px;
            border: 1px solid var(--light);
            background: white;
            border-radius: 20px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.3s;
        }}

        .feedback-btn:hover {{
            border-color: var(--primary);
            color: var(--primary);
        }}

        .feedback-btn.positive:hover {{
            background: #d1fae5;
            border-color: #10b981;
            color: #065f46;
        }}

        .feedback-btn.negative:hover {{
            background: #fee2e2;
            border-color: #ef4444;
            color: #991b1b;
        }}

        .card {{
            background: white;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            overflow: hidden;
            margin-bottom: 20px;
        }}

        .card-header {{
            padding: 20px;
            border-bottom: 1px solid var(--light);
            font-weight: 600;
            font-size: 1.1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .card-body {{
            padding: 20px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            padding: 24px;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            text-align: center;
        }}

        .stat-card .icon {{
            font-size: 40px;
            margin-bottom: 12px;
        }}

        .stat-card .value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary);
        }}

        .stat-card .label {{
            color: var(--gray);
            font-size: 0.9rem;
            margin-top: 4px;
        }}

        .table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .table th, .table td {{
            padding: 14px;
            text-align: left;
            border-bottom: 1px solid var(--light);
        }}

        .table th {{
            font-weight: 600;
            color: var(--gray);
            font-size: 0.85rem;
            text-transform: uppercase;
        }}

        .table tr:hover {{
            background: var(--light);
        }}

        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            border-radius: var(--radius);
            font-weight: 500;
            font-size: 0.9rem;
            cursor: pointer;
            border: none;
            text-decoration: none;
            transition: all 0.3s;
        }}

        .btn-primary {{
            background: var(--primary);
            color: white;
        }}

        .btn-primary:hover {{
            background: var(--primary-dark);
        }}

        .btn-danger {{
            background: var(--danger);
            color: white;
        }}

        .btn-sm {{
            padding: 6px 12px;
            font-size: 0.8rem;
        }}

        .form-group {{
            margin-bottom: 20px;
        }}

        .form-label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }}

        .form-control {{
            width: 100%;
            padding: 12px 16px;
            border: 2px solid var(--light);
            border-radius: var(--radius);
            font-size: 1rem;
        }}

        .form-control:focus {{
            outline: none;
            border-color: var(--primary);
        }}

        textarea.form-control {{
            min-height: 100px;
            resize: vertical;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .badge-primary {{ background: #e0e7ff; color: #4338ca; }}
        .badge-success {{ background: #d1fae5; color: #065f46; }}
        .badge-warning {{ background: #fef3c7; color: #92400e; }}
        .badge-danger {{ background: #fee2e2; color: #991b1b; }}

        .typing {{
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 12px 18px;
            background: white;
            border-radius: var(--radius);
            width: fit-content;
            box-shadow: var(--shadow);
        }}

        .typing span {{
            width: 8px;
            height: 8px;
            background: var(--gray);
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }}

        .typing span:nth-child(2) {{ animation-delay: 0.2s; }}
        .typing span:nth-child(3) {{ animation-delay: 0.4s; }}

        @keyframes typing {{
            0%, 60%, 100% {{ transform: translateY(0); }}
            30% {{ transform: translateY(-10px); }}
        }}

        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        code {{
            background: var(--light);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
        }}

        @media (max-width: 768px) {{
            .header h1 {{ font-size: 1.8rem; }}
            .chat-messages {{ height: 400px; }}
            .message-content {{ max-width: 85%; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .nav {{ gap: 6px; }}
            .nav a {{ padding: 8px 14px; font-size: 0.8rem; }}
        }}

        .chat-messages::-webkit-scrollbar {{
            width: 6px;
        }}

        .chat-messages::-webkit-scrollbar-track {{
            background: transparent;
        }}

        .chat-messages::-webkit-scrollbar-thumb {{
            background: var(--gray);
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🤖 NLP Chatbot</h1>
            <p>Умный чат-бот с обработкой естественного языка</p>
            <nav class="nav">
                <a href="/" class="{'active' if title == 'Чат' else ''}">💬 Чат</a>
                <a href="/stats" class="{'active' if title == 'Статистика' else ''}">📊 Статистика</a>
                <a href="/train" class="{'active' if title == 'Обучение' else ''}">🧠 Обучение</a>
                <a href="/test" class="{'active' if title == 'Тестирование' else ''}">🧪 Тест</a>
                <a href="/history" class="{'active' if title == 'История' else ''}">📜 История</a>
                <a href="/export" class="{'active' if title == 'Экспорт/Импорт' else ''}">📤 Экспорт</a>
                <a href="/docs-custom" class="{'active' if title == 'API Документация' else ''}">📚 API</a>
            </nav>
        </header>

        {content}
    </div>

    <script>
        function scrollToBottom() {{
            const messages = document.getElementById('chat-messages');
            if (messages) {{
                messages.scrollTop = messages.scrollHeight;
            }}
        }}

        window.onload = scrollToBottom;
    </script>
</body>
</html>
"""


# ═══════════════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
