# MATRIX&GROW Telegram Bot
# Renders psychomatrix exactly in the provided layout mock.
# Counting rules:
# - Base digits: date digits DDMMYYYY (zeros ignored for sector counts)
# - Additional numbers:
#     A1 = sum(all date digits)
#     A2 = sum(digits of A1)
#     A3 = A1 - 2 * (first day digit; if day starts with 0 use next)
#     A4 = sum(digits of A3)
# - Sector mapping:
#   1→ХАРАКТЕР, 2→ЕНЕРГІЯ, 3→ІНТЕРЕС, 4→ЗДОРОВ’Я, 5→ЛОГІКА, 6→ПРАЦЯ,
#   7→УДАЧА, 8→ОБОВ’ЯЗОК, 9→ПАМ’ЯТЬ
# - Derived lines:
#   Темперамент = 3 + 5 + 7
#   Сімʼя       = 2 + 5 + 8
#   Побут       = 4 + 5 + 6
#   Звички      = 3 + 6 + 9
#   Ціль        = 1 + 4 + 7
# - Life path number: reduce A1 to one digit, unless A2 == 11 (keep 11)
#
# Environment:
#   BOT_TOKEN in env vars (Replit "Secrets")
#
# Button:
#   links to @margosha_3811 chat by default.

import io, os, re
from datetime import datetime
from dateutil import parser
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters
from PIL import Image, ImageDraw, ImageFont

TOKEN = os.getenv("BOT_TOKEN")
OWNER_USERNAME = "margosha_3811"
OWNER_USER_ID = None  # optional numeric id
ASK_NAME, ASK_DOB = range(2)

# ---------- helpers ----------
def owner_link() -> str:
    if OWNER_USER_ID:
        return f"tg://user?id={int(OWNER_USER_ID)}"
    if OWNER_USERNAME:
        return f"https://t.me/{OWNER_USERNAME}"
    return "https://t.me/"

def digits_of_number(n: int):
    return [int(ch) for ch in str(abs(int(n)))]

def reduce_to_digit(n: int) -> int:
    while n > 9 and n != 11:
        n = sum(digits_of_number(n))
    return n

def parse_birthdate(text: str) -> datetime:
    m = re.match(r"^\s*(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})\s*$", text)
    if m:
        d, mth, y = map(int, m.groups())
        return datetime(y, mth, d)
    return parser.parse(text, dayfirst=True, fuzzy=True)

def additional_numbers(dt: datetime):
    date_digits = [int(ch) for ch in f"{dt.day:02d}{dt.month:02d}{dt.year}"]
    A1 = sum(date_digits)
    A2 = sum(digits_of_number(A1))
    day_s = f"{dt.day:02d}"
    first = int(day_s[0]) if day_s[0] != "0" else int(day_s[1])
    A3 = A1 - 2*first
    A4 = sum(digits_of_number(A3))
    return A1, A2, A3, A4

def lifepath_number(dt: datetime) -> int:
    A1, A2, *_ = additional_numbers(dt)
    if A2 == 11:
        return 11
    return reduce_to_digit(A1)

def counts_including_additionals(dt: datetime):
    counts = {i: 0 for i in range(1,10)}
    base = [int(ch) for ch in f"{dt.day:02d}{dt.month:02d}{dt.year}" if ch != '0']
    A1,A2,A3,A4 = additional_numbers(dt)
    extra = []
    for n in (A1,A2,A3,A4):
        extra += [d for d in digits_of_number(n) if d != 0]
    for d in base + extra:
        counts[d] += 1
    return counts

def derived_lines(counts: dict):
    return {
        "Темперамент": counts[3] + counts[5] + counts[7],
        "Сімʼя":        counts[2] + counts[5] + counts[8],
        "Побут":        counts[4] + counts[5] + counts[6],
        "Звички":       counts[3] + counts[6] + counts[9],
        "Ціль":         counts[1] + counts[4] + counts[7],
    }

# ---------- drawing ----------
def get_font(size=22):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
              "/Library/Fonts/Arial Unicode.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()

RED = (200, 60, 56)         # close to your mock
BEIGE = (245, 236, 228)
TEXT_DARK = (40, 40, 40)
WHITE = (255, 255, 255)

def draw_centered(draw, box, text, font, fill=TEXT_DARK):
    x0,y0,x1,y1 = box
    w,h = draw.textbbox((0,0), text, font=font)[2:4]
    draw.text((x0+(x1-x0-w)/2, y0+(y1-y0-h)/2), text, font=font, fill=fill)

def rounded(draw, x0,y0,x1,y1, r, fill):
    draw.rounded_rectangle([x0,y0,x1,y1], radius=r, fill=fill)

def make_matrix_image(name: str, dt: datetime) -> bytes:
    counts = counts_including_additionals(dt)
    lines = derived_lines(counts)
    lp = lifepath_number(dt)

    W,H = 1080, 1360  # aspect similar to your example
    img = Image.new("RGB", (W,H), WHITE)
    d = ImageDraw.Draw(img)

    font_lbl = get_font(34)
    font_val = get_font(40)
    font_head = get_font(36)
    font_foot = get_font(32)

    margin = 46
    gap = 24
    cell_w = (W - 2*margin - 3*gap) // 4   # 4 columns
    cell_h = 120

    # --- Row 1: headers (4 red cells) ---
    headers = [("Ім’я", name or "—"), ("Дата народження", dt.strftime("%d.%m.%Y")),
               ("ЧИСЛО ДОЛІ", str(lp)), ("ТЕМПЕРАМЕНТ", str(lines["Темперамент"]))]
    y = margin
    for i,(title,val) in enumerate(headers):
        x = margin + i*(cell_w+gap)
        rounded(d, x, y, x+cell_w, y+cell_h, 22, RED)
        draw_centered(d, (x, y+10, x+cell_w, y+58), title, font_head, WHITE)
        draw_centered(d, (x, y+60, x+cell_w, y+cell_h-8), val if val!="0" else "—", font_val, WHITE)

    # --- Main 3x3 grid (beige, with right column red for Ціль/Сімʼя/Звички) ---
    labels_1_9 = {
        1:"ХАРАКТЕР", 2:"ЕНЕРГІЯ", 3:"ІНТЕРЕС",
        4:"ЗДОРОВ’Я", 5:"ЛОГІКА", 6:"ПРАЦЯ",
        7:"УДАЧА", 8:"ОБОВ’ЯЗОК", 9:"ПАМ’ЯТЬ"
    }
    order = [[1,4,7],[2,5,8],[3,6,9]]  # visual map
    grid_top = y + cell_h + gap
    cell2 = 210

    for r in range(3):
        for c in range(3):
            digit = order[r][c]
            x = margin + c*(cell2+gap)
            y2 = grid_top + r*(cell2+gap)
            bg = BEIGE
            rounded(d, x, y2, x+cell2, y2+cell2, 26, bg)
            draw_centered(d, (x, y2+28, x+cell2, y2+90), labels_1_9[digit], font_lbl, TEXT_DARK)
            val = counts[digit]
            draw_centered(d, (x, y2+100, x+cell2, y2+cell2-16), str(val) if val>0 else "—", font_val, TEXT_DARK)

    # Right column (derived) as red cards aligned with grid rows
    right_x = margin + 2*(cell2+gap) + (W - margin - (margin + 3*(cell2+gap) - gap) - cell2)
    # But easier: compute based on 4th column from layout
    fourth_col_x = margin + 3*(cell_w+gap)  # align to first row
    # place red tall boxes for Ціль, Сім'я, Звички next to rows 1..3
    derived_labels = ["ЦІЛЬ","СІМ'Я","ЗВИЧКИ"]
    derived_keys   = ["Ціль","Сімʼя","Звички"]
    for i,(lab,key) in enumerate(zip(derived_labels, derived_keys)):
        x = margin + 3*(cell2+gap)  # to the right of 3x3
        y2 = grid_top + i*(cell2+gap)
        rounded(d, x, y2, x+cell2, y2+cell2, 26, RED)
        draw_centered(d, (x, y2+28, x+cell2, y2+90), lab, font_lbl, WHITE)
        val = lines[key]
        draw_centered(d, (x, y2+100, x+cell2, y2+cell2-16), str(val) if val>0 else "—", font_val, WHITE)

    # --- Bottom row: left red blank, middle red "ПОБУТ", right wide red Instagram ---
    bottom_y = grid_top + 3*(cell2+gap) + gap
    # left red blank
    x0 = margin
    rounded(d, x0, bottom_y, x0+cell2, bottom_y+cell_h, 26, RED)
    # middle red ПОБУТ
    x1 = x0 + cell2 + gap
    rounded(d, x1, bottom_y, x1+cell2, bottom_y+cell_h, 26, RED)
    draw_centered(d, (x1, bottom_y+18, x1+cell2, bottom_y+60), "ПОБУТ", font_head, WHITE)
    draw_centered(d, (x1, bottom_y+58, x1+cell2, bottom_y+cell_h-8), str(lines["Побут"]) if lines["Побут"]>0 else "—", font_val, WHITE)
    # right wide Instagram
    x2 = x1 + cell2 + gap
    wide_w = W - margin - x2
    rounded(d, x2, bottom_y, x2+wide_w, bottom_y+cell_h, 26, RED)
    draw_centered(d, (x2, bottom_y+18, x2+wide_w, bottom_y+60), "Instagram", font_head, WHITE)
    draw_centered(d, (x2, bottom_y+58, x2+wide_w, bottom_y+cell_h-8), "@margosha_3811", font_foot, WHITE)

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio.getvalue()

# ---------- bot flow ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Я порахую твою психоматрицю і пришлю картинку у твоєму стилі.\n\n"
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
            raise ValueError()
    except Exception:
        await update.message.reply_text("Не зміг прочитати дату 🤔 Спробуй так: 01.11.1998")
        return ASK_DOB

    name = context.user_data.get("name","")
    pic = make_matrix_image(name, dt)

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Замовити розбір у Telegram", url=owner_link())]]
    )
    await update.message.reply_photo(photo=pic, caption="Готово! Хочеш детальний розбір — натисни кнопку 👇", reply_markup=keyboard)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано. Для початку — /start")
    return ConversationHandler.END

def main():
    if not TOKEN:
        raise SystemExit("❌ BOT_TOKEN env var is not set")
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

