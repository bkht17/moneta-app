"""Kind and category rules for imported rows.

Categories are a starting point only: the student can change any of them (F2), and
that changes category totals but never total spending.
"""

from ..models import Kind

CASH_CATEGORY = "Cash, unspecified"
TRANSFERS_TO_PEOPLE = "Transfers to people"
OTHER = "Other"

CATEGORIES = [
    "Groceries",
    "Cafés",
    "Food delivery",
    "Transport",
    "Study",
    "Subscriptions",
    "Clothing",
    "Health",
    "Mobile and internet",
    "Entertainment",
    TRANSFERS_TO_PEOPLE,
    OTHER,
]

KEYWORDS = [
    ("Groceries", ("magnum", "small", "galmart", "anvar", "ramstore", "супермаркет")),
    ("Food delivery", ("glovo", "wolt", "yandex eda", "яндекс еда", "chocofood")),
    (
        "Transport",
        ("yandex go", "yandex.go", "taxi", "такси", "onay", "uber", "indrive"),
    ),
    ("Cafés", ("coffee", "кофе", "cafe", "café", "кафе", "starbucks", "lanzhou")),
    ("Study", ("copy", "print", "book", "kitap", "univer", "kbtu", "coursera")),
    ("Subscriptions", ("spotify", "yandex plus", "netflix", "apple.com", "icloud")),
    ("Clothing", ("zara", "lc waikiki", "clothing", "одежда", "adidas", "nike")),
    ("Health", ("аптека", "pharm", "clinic", "клиника")),
    (
        "Mobile and internet",
        ("beeline", "kcell", "activ", "tele2", "altel", "kazakhtelecom"),
    ),
    ("Entertainment", ("kino", "cinema", "steam", "playstation")),
]


def kind_for(operation, amount):
    op = operation.lower()
    if op.startswith("снятие"):
        return Kind.WITHDRAWAL
    if op.startswith("возврат"):
        return Kind.REFUND
    if op.startswith("перевод"):
        return Kind.TRANSFER_IN if amount > 0 else Kind.TRANSFER_OUT
    if op.startswith("пополнение"):
        return Kind.TRANSFER_IN
    if amount > 0:
        return Kind.INCOME
    return Kind.PURCHASE


def category_for(kind, description):
    if kind == Kind.TRANSFER_OUT:
        return TRANSFERS_TO_PEOPLE
    lowered = description.lower()
    for category, words in KEYWORDS:
        if any(word in lowered for word in words):
            return category
    return OTHER
