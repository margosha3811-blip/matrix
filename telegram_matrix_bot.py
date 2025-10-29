# Telegram Psychomatrix Bot (Matrix of Numbers) — MATRIX&GROW
# Python 3.10+ | Libraries: python-telegram-bot==20.7, python-dateutil, pillow
#
# Local run:
#   pip install -r requirements.txt
#   export BOT_TOKEN="YOUR_TOKEN"  # macOS/Linux
#   set BOT_TOKEN=YOUR_TOKEN       # Windows PowerShell
#   python telegram_matrix_bot.py
#
# Render.com:
#   Add env var BOT_TOKEN in service settings.

import io, os, re
from datetime import datetime
from dateutil import parser
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters

from PIL import Image, ImageDraw, ImageFont

# ========= SETTINGS =========
TOKEN = os.getenv("BOT_TOKEN")  # <-- keep your token in the BOT_TOKEN env var
OWNER_CONTACT = "https://t.me/margosha_3811"

ASK_NAME, ASK_DOB = range(2)

# ========= UTILITIES =========
def only_digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())

def reduce_to_digit(n: int) -> int:
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n

def parse_birthdate(text: str) -> datetime:
    """
    Acceptable inputs:
    - 01.11.1998
    - 01-11-1998
    - 1/11/1998
    - 01 листопада 1998 / 01 Листопад 1998 / 01 Nov 1998 (dateutil parses)
    """
    m = re.match(r"^\s*(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})\s*$", text)
    if m:
        d, mth, y = map(int, m.groups())
        return datetime(y, mth, d)
    return parser.parse(text, dayfirst=True, fuzzy=True)

def lifepath_number(dt: datetime) -> int:
    digits = list(str(dt.day) + str(dt.month) + str(dt.year))
    return reduce_to_digit(sum(int(d) for d in digits))

def pythagoras_counts(dt: datetime) -> dict:
    s = only_digits(f"{dt.day:02d}{dt.month:02d}{dt.year}")
    counts = {i: 0 for i in range(1, 10)}
    for ch in s:
        if ch != "0":
            counts[int(ch)] += 1
    return counts

# Derived indicators
def derived_lines(counts: dict) -> dict:
    return {
        "Темперамент": counts[3] + counts[6] + counts[9],  # right column
        "Сімʼя":        counts[2] + counts[5] + counts[8],  # middle column
        "Побут":        counts[4] + counts[5] + counts[6],  # middle row
        "Звички":       counts[1] + counts[5] + counts[9],  # diagonal 1-5-9
        "Ціль":         counts[3] + counts[5] + counts[7],  # diagonal 3-5-7
    }

# ========= IMAGE RENDER =========
def get_font(size=22):
    # Try common fonts with Cyrillic; fallback to default
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()

def draw_centered_text(draw, box, text, font, fill=(34,34,34)):
    x0, y0, x1, y1 = box
    bbox = draw.textbbox((0,0), text, font=font)
    w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text((x0 + (x1-x0-w)/2, y0 + (y1-y0-h)/2), text, font=font, fill=fill)

def make_matrix_image(name: str, dt: datetime) -> bytes:
    counts = pythagoras_counts(dt)
    lp = lifepath_number(dt)
    lines = derived_lines(counts)

    labels_1_9 = {
        1: "ХАРАКТЕР", 2: "ЕНЕРГІЯ", 3: "ІНТЕРЕС",
        4: "ЗДОРОВ’Я", 5: "ЛОГІКА", 6: "ПРАЦЯ",
        7: "УДАЧА",    8: "ОБОВ’ЯЗОК", 9: "ПАМ’ЯТЬ"
    }

    W, H = 900, 1400
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)

    font_h1 = get_font(40)
    font_h2 = get_font(28)
    font_body = get_font(24)
    font_small = get_font(20)

    # Header
    d.text((40, 30), "Психоматриця", font=font_h1, fill=(34,34,34))
    d.text((40, 90), f"Ім’я: {name}", font=font_body, fill=(34,34,34))
    d.text((40, 125), f"Дата нар.: {dt.strftime('%d.%m.%Y')}", font=font_body, fill=(34,34,34))
    d.text((40, 160), f"Число долі: {lp}", font=font_body, fill=(34,34,34))

    # Grid 3x3
    grid_top = 220
    grid_left = 60
    cell = 230
    gap = 18

    # Layout:
    # 1 4 7
    # 2 5 8
    # 3 6 9
    order = [
        [1,4,7],
        [2,5,8],
        [3,6,9]
    ]

    for r in range(3):
        for c in range(3):
            digit = order[r][c]
            x0 = grid_left + c*(cell+gap)
            y0 = grid_top  + r*(cell+gap)
            x1 = x0 + cell
            y1 = y0 + cell

            # background color
            bg = (232,78,78) if digit in (1,2,3,7,8,9) else (245,236,228)
            d.rounded_rectangle([x0, y0, x1, y1], radius=24, fill=bg)

            # label + value
            draw_centered_text(d, (x0, y0+30, x1, y0+90), labels_1_9[digit], font=font_small, fill=(34,34,34))
            draw_centered_text(
                d, (x0, y0+110, x1, y1-40),
                str(counts[digit]) if counts[digit] > 0 else "—",
                font=get_font(36),
                fill=(255,255,255) if bg==(232,78,78) else (34,34,34)
            )

    # Derived sections (5 boxes)
    sec_top = grid_top + 3*(cell+gap) + 30
    box_w = (W - 2*grid_left - gap) // 2
    box_h = 120
    boxes = [
        ("ТЕМПЕРАМЕНТ", lines["Темперамент"]),
        ("СІМʼЯ",        lines["Сімʼя"]),
        ("ПОБУТ",        lines["Побут"]),
        ("ЗВИЧКИ",       lines["Звички"]),
        ("ЦІЛЬ",         lines["Ціль"]),
    ]
    for i, (lbl, val) in enumerate(boxes):
        r = i // 2
        c = i % 2
        x0 = grid_left + c*(box_w + gap)
        y0 = sec_top + r*(box_h + gap)
        x1 = x0 + box_w
        y1 = y0 + box_h

        bg = (232,78,78) if i in (0,1,4) else (245,236,228)
        d.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=bg)
        draw_centered_text(d, (x0, y0+18, x1, y0+60), lbl, font=font_h2, fill=(255,255,255) if bg==(232,78,78) else (34,34,34))
        draw_centered_text(
            d, (x0, y0+60, x1, y1-10),
            str(val) if val>0 else "—",
            font=get_font(34),
            fill=(255,255,255) if bg==(232,78,78) else (34,34,34)
        )

    # Footer
    d.text((W//2 - 200, H-60), "inst: @margosha_3811", font=font_small, fill=(153,153,153))

    # To bytes
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio.getvalue()

# ========= HANDLERS =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Я порахую твою психоматрицю і пришлю картинку.\n\n"
        "Напиши, будь ласка, своє *ім’я*.",
        parse_mode="Markdown"
    )
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("Занадто коротке ім’я. Введи ще раз 🙂")
        return ASK_NAME
    context.user_data["name"] = name
    await update.message.reply_text(
        "Дякую! Тепер введи *дату народження* у форматі `дд.мм.рррр` "
        "або текстом (наприклад, 1 листопада 1998).",
        parse_mode="Markdown"
    )
    return ASK_DOB

async def ask_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        dt = parse_birthdate(text)
        if dt.year < 1900 or dt > datetime.now():
            raise ValueError("bad date")
    except Exception:
        await update.message.reply_text("Не зміг прочитати дату 🤔 Спробуй так: 01.11.1998")
        return ASK_DOB

    name = context.user_data.get("name","")
    pic = make_matrix_image(name, dt)

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Замовити розбір у Telegram", url=OWNER_CONTACT)]]
    )
    await update.message.reply_photo(photo=pic, caption="Готово! Хочеш детальний розбір — натисни кнопку 👇", reply_markup=keyboard)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано. Для початку — /start")
    return ConversationHandler.END

def main():
    if not TOKEN:
        raise SystemExit("❌ BOT_TOKEN env var is not set. Please set BOT_TOKEN and restart.")
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_DOB:  [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_dob)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("cancel", cancel))

    app.run_polling()

if __name__ == "__main__":
    main()
