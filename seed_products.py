"""
إضافة المنتجات الأساسية من كتالوج نيو دنت
"""
from app.database import SessionLocal, Product, Category, init_db

init_db()
db = SessionLocal()

# تصنيفات
categories = {
    "مواد طبع": "Impression Materials",
    "جبس وشمع": "Stone & Wax",
    "بوندات": "Bonding Agents",
    "حشو مؤقت": "Temporary Filling",
    "تلميع": "Polishing",
    "مستلزمات طبية": "Medical Supplies",
    "بنج وإبر": "Topical & Needles",
    "فلوبول": "Flowable",
    "كومبوزت": "Composite",
    "أتش": "Etch",
    "كونترا": "Handpieces",
}

cat_ids = {}
for ar, en in categories.items():
    c = db.query(Category).filter(Category.name == ar).first()
    if not c:
        c = Category(name=ar, name_en=en)
        db.add(c)
        db.flush()
    cat_ids[ar] = c.id

# منتجات أساسية (عينة من الكتالوج)
products = [
    ("نابكن", "Napkin", 80, "مستلزمات طبية"),
    ("رول تغليف", "Wrapping Roll", 150, "مستلزمات طبية"),
    ("جوانتي لاتكس", "Gloves Latex", 165, "مستلزمات طبية"),
    ("رول 7.5 سم", "Roll 7.5 cm", 300, "مستلزمات طبية"),
    ("رول 10 سم", "Roll 10 cm", 400, "مستلزمات طبية"),
    ("رابر بيس زيتابلس", "Rubber Base Zetaplus", 2150, "مواد طبع"),
    ("رابر بيس سلاكسي", "Rubber Base Salxil", 1950, "مواد طبع"),
    ("الجنيت زيتالجين", "Alginate Zetalgin", 300, "مواد طبع"),
    ("الجنيت تروبيكال", "Alginate Tropicalgin", 435, "مواد طبع"),
    ("الجنيت كيفكس", "Alginate Cavex", 490, "مواد طبع"),
    ("جبس كوري", "Korean Dental Stone", 70, "جبس وشمع"),
    ("جبس مصري", "Egyptian Dental Stone", 25, "جبس وشمع"),
    ("بوند الترا 4 مل", "Bond Ultra 4ml", 475, "بوندات"),
    ("بوند بيسكو 4 مل", "Bond Bisco 4ml", 2200, "بوندات"),
    ("بوند تيترك إن", "Bond Tetric N", 2700, "بوندات"),
    ("حشو مؤقت جلاكسي", "Temporary Filling Galaxy", 75, "حشو مؤقت"),
    ("حشو مؤقت أورافيل", "Temporary Filling Orafil", 195, "حشو مؤقت"),
    ("معجون تلميع ADS", "Polishing Paste ADS", 195, "تلميع"),
    ("معجون تلميع روبي", "Polishing Paste Ruby", 80, "تلميع"),
    ("زيكال", "Zical", 500, "مستلزمات طبية"),
    ("قطن رول", "Cotton Roll", 155, "مستلزمات طبية"),
    ("ماسك", "Mask", 50, "مستلزمات طبية"),
    ("بنج موضعي أمريكي", "Topical Gel USA", 100, "بنج وإبر"),
    ("إبر بنج إيطالي", "Needle Speed Jet", 230, "بنج وإبر"),
    ("أملجم إيطالي", "Amalgam World Work", 3250, "بنج وإبر"),
    ("فلوبول دي فيل", "Flowable D Fill", 450, "فلوبول"),
    ("فلوبول اسبايدنت", "Flowable Spedint", 300, "فلوبول"),
    ("كومبوزت دي فيل", "Composite D Fill", 450, "كومبوزت"),
    ("كومبوزت شوفو", "Composite Shofu", 1100, "كومبوزت"),
    ("كومبوزت 3M", "Composite 3M", 1300, "كومبوزت"),
    ("كومبوزت تيترك إن", "Composite Tetric N", 1300, "كومبوزت"),
    ("أتش ألماني", "Etch Gel Germany", 185, "أتش"),
    ("كونترا أبل هاي", "Contra Apple High", 1575, "كونترا"),
    ("كونترا وود بيكر", "Contra Woodpecker", 2450, "كونترا"),
    ("كونترا بانا ماكس", "Contra Bana Max", 4800, "كونترا"),
]

for name, name_en, price, cat in products:
    exists = db.query(Product).filter(Product.name == name).first()
    if not exists:
        p = Product(
            name=name,
            name_en=name_en,
            sell_price=price,
            cost_price=round(price * 0.7, 2),
            stock_qty=20,
            min_stock=5,
            category_id=cat_ids.get(cat),
            unit="قطعة"
        )
        db.add(p)

db.commit()
print(f"تم إضافة المنتجات بنجاح!")
print(f"عدد المنتجات: {db.query(Product).count()}")
db.close()
