from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./nds_accounting.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    full_name = Column(String(100))
    hashed_password = Column(String(200))
    role = Column(String(20), default="staff")  # admin / staff / customer
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)  # لو عميل
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", foreign_keys=[customer_id])


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True)
    name_en = Column(String(100), nullable=True)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True)
    name_en = Column(String(200), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    unit = Column(String(50), default="قطعة")
    cost_price = Column(Float, default=0)          # سعر الشراء
    sell_price = Column(Float, default=0)          # سعر البيع
    stock_qty = Column(Float, default=0)           # الرصيد الحالي
    min_stock = Column(Float, default=5)           # حد إعادة الطلب
    barcode = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category")


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), index=True)
    phone = Column(String(30), nullable=True)
    address = Column(String(250), nullable=True)
    notes = Column(Text, nullable=True)
    balance = Column(Float, default=0)  # المبلغ المستحق عليه
    created_at = Column(DateTime, default=datetime.utcnow)


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), index=True)
    phone = Column(String(30), nullable=True)
    address = Column(String(250), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SaleInvoice(Base):
    __tablename__ = "sale_invoices"
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    total_amount = Column(Float, default=0)
    discount = Column(Float, default=0)
    paid_amount = Column(Float, default=0)
    payment_method = Column(String(50), default="نقدي")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    customer = relationship("Customer")
    items = relationship("SaleItem", back_populates="invoice", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("sale_invoices.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Float, default=1)
    unit_price = Column(Float, default=0)
    total = Column(Float, default=0)

    invoice = relationship("SaleInvoice", back_populates="items")
    product = relationship("Product")


class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    total_amount = Column(Float, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    supplier = relationship("Supplier")
    items = relationship("PurchaseItem", back_populates="invoice", cascade="all, delete-orphan")


class PurchaseItem(Base):
    __tablename__ = "purchase_items"
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("purchase_invoices.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Float, default=1)
    unit_cost = Column(Float, default=0)
    total = Column(Float, default=0)

    invoice = relationship("PurchaseInvoice", back_populates="items")
    product = relationship("Product")


class StockMovement(Base):
    __tablename__ = "stock_movements"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    movement_type = Column(String(20))  # in / out / adjust
    quantity = Column(Float)
    reference = Column(String(100), nullable=True)  # رقم الفاتورة أو ملاحظة
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    product = relationship("Product")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
