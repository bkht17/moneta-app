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


def kaspi_lines_en(year=2026, month=10, last_day=15):
    """The same Kaspi Gold statement as the English version of the bank's PDF."""
    yy = f"{year % 100:02d}"
    mm = f"{month:02d}"
    rows = [
        ("02", "+ 42 000,00", "Replenishment", "Stipend KBTU"),
        ("03", "- 6 200,00", "Purchases", "MAGNUM CASH&CARRY"),
        ("04", "+ 5 000,00", "Replenishment", "At Kaspi ATM"),
        ("05", "- 20 000,00", "Transfers", "Halyk Bank *5678"),
        ("09", "- 4 600,00", "Purchases", "Додо пицца"),
        ("14", "- 10 000,00", "Withdrawals", "Kaspi ATM"),
    ]
    return [
        "To Whom It May Concern",
        "Kaspi Gold",
        f"balance statement for the period from 01.{mm}.{yy} to {last_day:02d}.{mm}.{yy}",
        "DEMO STUDENT",
        "Card number: *1234",
        "Transaction summary:",
        "Purchases - 10 800,00 ₸",
        "Date Amount Transaction Details",
        *[
            f"{d}.{mm}.{yy} {amount} ₸ {op} {details}"
            for d, amount, op, details in rows
        ],
    ]


def kaspi_lines_kk(year=2026, month=10, last_day=15):
    """A Kaspi Gold statement in the Kazakh-language layout."""
    yy = f"{year % 100:02d}"
    mm = f"{month:02d}"
    rows = [
        ("02", "+ 42 000,00", "Толықтыру", "Стипендия KBTU"),
        ("03", "- 6 200,00", "Сатып алу", "MAGNUM CASH&CARRY"),
        ("07", "- 1 800,00", "Сатып алу", "Yandex Go"),
        ("09", "- 4 600,00", "Сатып алу", "Glovo"),
        ("14", "- 10 000,00", "Ақша шешу", "Kaspi банкоматы"),
    ]
    return [
        "«Kaspi Bank» АҚ",
        "Kaspi Gold бойынша үзінді көшірме",
        f"Кезең: 01.{mm}.{yy} бастап {last_day:02d}.{mm}.{yy} дейін",
        "Демо Студент",
        "Карта нөмірі: *1234",
        "Күні Сомасы Операция Толығырақ",
        *[
            f"{d}.{mm}.{yy} {amount} ₸ {op} {details}"
            for d, amount, op, details in rows
        ],
    ]


def halyk_lines_kk(year=2026, month=10, last_day=18):
    """A Halyk card account statement in the Kazakh-language layout."""
    mm = f"{month:02d}"
    rows = [
        ("06", "Spotify жазылымы", "-2 000,00", "0,00", "2 000,00"),
        ("10", "Copy centre KBTU", "-3 000,00", "0,00", "3 000,00"),
        ("11", "Lanzhou cafe", "-4 500,00", "0,00", "4 500,00"),
    ]
    lines = [
        "«Қазақстан Халық Банкі» АҚ Halyk Bank",
        "Карт шоты бойынша үзінді көшірме",
        f"Кезең: 01.{mm}.{year} бастап {last_day:02d}.{mm}.{year} дейін",
        "Карта: Visa *5678",
        "Операция күні Өңдеу күні Операцияның сипаттамасы Сомасы Валюта "
        "Кіріс Шығыс Комиссия Карта №",
    ]
    for d, desc, op_amount, credit, debit in rows:
        processed = f"{int(d) + 1:02d}"
        lines.append(
            f"{d}.{mm}.{year} {processed}.{mm}.{year} {desc} {op_amount} KZT "
            f"{credit} {debit} 0,00 *5678"
        )
    lines.append("Барлығы: кіріс 0,00 шығыс 9 500,00")
    return lines


def halyk_lines_short(year=2026, month=10, last_day=18):
    """A Halyk statement with only date, description, signed amount and currency."""
    mm = f"{month:02d}"
    return [
        "Halyk Bank",
        "Card account statement",
        f"for the period from 01.{mm}.{year} to {last_day:02d}.{mm}.{year}",
        "Card: *5678",
        "Date Description Amount Currency",
        f"05.{mm}.{year} Top-up from Kaspi card 20 000,00 KZT",
        f"06.{mm}.{year} Spotify -2 000,00 KZT",
        f"12.{mm}.{year} Refund LC Waikiki 2 500,00 KZT",
        "Total: 20 500,00",
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
