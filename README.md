# MATRIX&GROW | Нумерологічний помічник (Telegram Bot)

Цей бот рахує психоматрицю (1–9) + показники: **Темперамент, Сімʼя, Звички, Побут, Ціль** і повертає **картинку** з результатом.

## Швидкий старт (локально)
```bash
pip install -r requirements.txt
export BOT_TOKEN="ВАШ_ТОКЕН"   # macOS/Linux
# або: set BOT_TOKEN=ВАШ_ТОКЕН  # Windows PowerShell
python telegram_matrix_bot.py
```

## Деплой на Render.com
1. Запушити цей репозиторій на GitHub.
2. На Render створити **Worker** з цього репозиторію.
3. Додати Environment Variable: `BOT_TOKEN` = ваш токен з BotFather.
4. Start Command: `bash start.sh`.
5. Готово — бот працює 24/7.

## Файли
- `telegram_matrix_bot.py` — код бота
- `requirements.txt` — залежності
- `start.sh` — команда запуску
- `render.yaml` — конфіг для Render (не обовʼязковий)
