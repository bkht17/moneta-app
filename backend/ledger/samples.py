"""Synthetic Kaspi and Halyk statements in the layouts the parsers expect.

They mirror the reference case from Assignment 7 (F2-AC1, F3-AC1/AC2): budget
100,000 ₸, 8,000 ₸ cash, net spending 35,000 ₸ through 15 Oct, Halyk rows for
16–18 Oct outside the main total. All names and numbers are invented test data.
"""

from pathlib import Path

FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
)


def kaspi_lines(year=2026, month=10, last_day=15):
    yy = f"{year % 100:02d}"
    mm = f"{month:02d}"
    rows = [
        ("02", "+ 42 000,00", "Пополнение", "Стипендия KBTU"),
        ("03", "- 6 200,00", "Покупка", "MAGNUM CASH&CARRY"),
        ("05", "- 20 000,00", "Перевод", "Halyk Bank *5678"),
        ("07", "- 1 800,00", "Покупка", "Yandex Go"),
        ("09", "- 4 600,00", "Покупка", "Glovo"),
        ("12", "- 1 200,00", "Покупка", "Coffee Boom"),
        ("12", "- 1 200,00", "Покупка", "Coffee Boom"),
        ("14", "- 10 000,00", "Снятие", "Банкомат Kaspi Bank"),
    ]
    return [
        "АО «Kaspi Bank»",
        f"ВЫПИСКА по Kaspi Gold за период с 01.{mm}.{yy} по {last_day:02d}.{mm}.{yy}",
        "Демо Студент",
        "Номер карты: *1234",
        "Дата Сумма Операция Детали",
        *[
            f"{d}.{mm}.{yy} {amount} ₸ {op} {details}"
            for d, amount, op, details in rows
        ],
    ]


def halyk_lines(year=2026, month=10, last_day=18):
    mm = f"{month:02d}"
    rows = [
        ("05", "Пополнение с карты Kaspi", "20 000,00", "20 000,00", "0,00"),
        ("06", "Spotify subscription", "-2 000,00", "0,00", "2 000,00"),
        ("10", "Copy centre KBTU", "-3 000,00", "0,00", "3 000,00"),
        ("11", "Lanzhou cafe", "-4 500,00", "0,00", "4 500,00"),
        ("13", "LC Waikiki", "-2 500,00", "0,00", "2 500,00"),
        ("16", "MAGNUM", "-2 100,00", "0,00", "2 100,00"),
        ("17", "Yandex Go", "-1 500,00", "0,00", "1 500,00"),
        ("18", "Coffee Boom", "-700,00", "0,00", "700,00"),
    ]
    lines = [
        "АО «Народный сберегательный банк Казахстана» Halyk Bank",
        "Выписка по карточному счету",
        f"за период с 01.{mm}.{year} по {last_day:02d}.{mm}.{year}",
        "Карта: Visa *5678",
        "Дата проведения операции Дата обработки операции Описание операции "
        "Сумма операции Валюта операции Приход Расход Комиссия № карточки",
    ]
    for d, desc, op_amount, credit, debit in rows:
        processed = f"{int(d) + 1:02d}"
        lines.append(
            f"{d}.{mm}.{year} {processed}.{mm}.{year} {desc} {op_amount} KZT "
            f"{credit} {debit} 0,00 *5678"
        )
    lines.append("Итого: приход 20 000,00 расход 18 300,00")
    return lines


def find_font():
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return path
    return None


def write_pdf(lines, path, font_path=None):
    """Write lines to a one-page PDF with a Cyrillic-capable TrueType font."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    font_path = font_path or find_font()
    if not font_path:
        raise RuntimeError("No Cyrillic TrueType font found; pass --font.")
    pdfmetrics.registerFont(TTFont("StatementFont", font_path))
    pdf = canvas.Canvas(str(path), pagesize=A4)
    pdf.setFont("StatementFont", 8)
    y = A4[1] - 40
    for line in lines:
        pdf.drawString(30, y, line)
        y -= 14
    pdf.save()
