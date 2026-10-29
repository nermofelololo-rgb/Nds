from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import os

from .database import (
    init_db, get_db, Product, Category, Customer, Supplier,
    SaleInvoice, SaleItem, PurchaseInvoice, PurchaseItem,
    StockMovement, User
)
from .auth import (
    hash_password, verify_password, create_session_token,
    get_current_user, require_staff, require_admin
)

app = FastAPI(title="نيو دنت - نظام المحاسبة والمخزون")

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
templates.env.auto_reload = True
templates.env.cache = None
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


@app.on_event("startup")
def startup():
    init_db()
    # إنشاء مستخدم افتراضي لو مش موجود
    db = next(get_db())
    if not db.query(User).filter(User.username == "admin").first():
        admin = User(
            username="admin",
            full_name="مدير النظام",
            hashed_password=hash_password("admin123"),
            role="admin"
        )
        db.add(admin)
        db.commit()
    db.close()



# ==================== تسجيل الدخول ====================

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(request, "login.html", {
            "error": "اسم المستخدم أو كلمة المرور غير صحيحة"
        })
    
    token = create_session_token(user.id, user.role)
    # توجيه حسب الدور
    if user.role == "customer":
        response = RedirectResponse("/portal", status_code=303)
    else:
        response = RedirectResponse("/", status_code=303)
    response.set_cookie("nds_session", token, httponly=True, max_age=60*60*12)
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("nds_session")
    return response


# ==================== بوابة العميل ====================

@app.get("/portal", response_class=HTMLResponse)
def customer_portal(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "customer":
        return RedirectResponse("/login", status_code=303)
    
    customer = db.query(Customer).get(user.customer_id) if user.customer_id else None
    invoices = []
    if customer:
        invoices = db.query(SaleInvoice).filter(
            SaleInvoice.customer_id == customer.id
        ).order_by(SaleInvoice.created_at.desc()).limit(20).all()
    
    return templates.TemplateResponse(request, "portal.html", {
        "user": user,
        "customer": customer,
        "invoices": invoices,
        "page": "portal"
    })


@app.get("/portal/products", response_class=HTMLResponse)
def portal_products(request: Request, db: Session = Depends(get_db), q: str = ""):
    user = get_current_user(request, db)
    if not user or user.role != "customer":
        return RedirectResponse("/login", status_code=303)
    
    query = db.query(Product).filter(Product.is_active == True)
    if q:
        query = query.filter(Product.name.contains(q) | Product.name_en.contains(q))
    products = query.order_by(Product.name).all()
    
    return templates.TemplateResponse(request, "portal_products.html", {
        "user": user,
        "products": products,
        "q": q,
        "page": "portal_products"
    })


@app.get("/portal/invoice/{invoice_id}", response_class=HTMLResponse)
def portal_invoice(invoice_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "customer":
        return RedirectResponse("/login", status_code=303)
    
    invoice = db.query(SaleInvoice).get(invoice_id)
    if not invoice or invoice.customer_id != user.customer_id:
        raise HTTPException(404, "الفاتورة غير موجودة")
    
    return templates.TemplateResponse(request, "sale_view.html", {
        "invoice": invoice,
        "page": "portal",
        "is_portal": True
    })


# ==================== الصفحات الرئيسية ====================

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if user.role == "customer":
        return RedirectResponse("/portal", status_code=303)
    
    products_count = db.query(Product).filter(Product.is_active == True).count()
    low_stock = db.query(Product).filter(Product.stock_qty <= Product.min_stock, Product.is_active == True).count()
    customers_count = db.query(Customer).count()
    today = datetime.now().date()
    today_sales = db.query(SaleInvoice).filter(
        SaleInvoice.created_at >= datetime.combine(today, datetime.min.time())
    ).count()
    
    low_stock_products = db.query(Product).filter(
        Product.stock_qty <= Product.min_stock,
        Product.is_active == True
    ).order_by(Product.stock_qty).limit(10).all()

    return templates.TemplateResponse(request, "dashboard.html", {
        "products_count": products_count,
        "low_stock": low_stock,
        "customers_count": customers_count,
        "today_sales": today_sales,
        "low_stock_products": low_stock_products,
        "page": "dashboard"
    })


# ==================== المنتجات ====================

@app.get("/products", response_class=HTMLResponse)
def products_list(request: Request, db: Session = Depends(get_db), q: str = ""):
    query = db.query(Product).filter(Product.is_active == True)
    if q:
        query = query.filter(Product.name.contains(q) | Product.name_en.contains(q))
    products = query.order_by(Product.name).all()
    categories = db.query(Category).all()
    return templates.TemplateResponse(request, "products.html", {
        "products": products,
        "categories": categories,
        "q": q,
        "page": "products"
    })


@app.post("/products/add")
def add_product(
    name: str = Form(...),
    name_en: str = Form(""),
    sell_price: float = Form(0),
    cost_price: float = Form(0),
    stock_qty: float = Form(0),
    min_stock: float = Form(5),
    unit: str = Form("قطعة"),
    category_id: int = Form(None),
    db: Session = Depends(get_db)
):
    product = Product(
        name=name,
        name_en=name_en or None,
        sell_price=sell_price,
        cost_price=cost_price,
        stock_qty=stock_qty,
        min_stock=min_stock,
        unit=unit,
        category_id=category_id if category_id else None
    )
    db.add(product)
    db.commit()
    return RedirectResponse("/products", status_code=303)


@app.post("/products/update/{product_id}")
def update_product(
    product_id: int,
    name: str = Form(...),
    sell_price: float = Form(0),
    cost_price: float = Form(0),
    min_stock: float = Form(5),
    db: Session = Depends(get_db)
):
    product = db.query(Product).get(product_id)
    if product:
        product.name = name
        product.sell_price = sell_price
        product.cost_price = cost_price
        product.min_stock = min_stock
        db.commit()
    return RedirectResponse("/products", status_code=303)


# ==================== المخزون ====================

@app.get("/inventory", response_class=HTMLResponse)
def inventory(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.is_active == True).order_by(Product.name).all()
    return templates.TemplateResponse(request, "inventory.html", {
        "products": products,
        "page": "inventory"
    })


@app.post("/inventory/adjust")
def adjust_stock(
    product_id: int = Form(...),
    quantity: float = Form(...),
    movement_type: str = Form(...),  # in / out / set
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    product = db.query(Product).get(product_id)
    if not product:
        raise HTTPException(404, "المنتج غير موجود")

    if movement_type == "in":
        product.stock_qty += quantity
        qty = quantity
    elif movement_type == "out":
        product.stock_qty -= quantity
        qty = -quantity
    else:  # set
        qty = quantity - product.stock_qty
        product.stock_qty = quantity

    movement = StockMovement(
        product_id=product_id,
        movement_type=movement_type,
        quantity=qty,
        notes=notes or "تعديل يدوي"
    )
    db.add(movement)
    db.commit()
    return RedirectResponse("/inventory", status_code=303)


# ==================== العملاء ====================

@app.get("/customers", response_class=HTMLResponse)
def customers_list(request: Request, db: Session = Depends(get_db)):
    customers = db.query(Customer).order_by(Customer.name).all()
    return templates.TemplateResponse(request, "customers.html", {
        "customers": customers,
        "page": "customers"
    })


@app.post("/customers/add")
def add_customer(
    name: str = Form(...),
    phone: str = Form(""),
    address: str = Form(""),
    db: Session = Depends(get_db)
):
    customer = Customer(name=name, phone=phone or None, address=address or None)
    db.add(customer)
    db.commit()
    return RedirectResponse("/customers", status_code=303)


# ==================== فواتير المبيعات ====================

@app.get("/sales", response_class=HTMLResponse)
def sales_list(request: Request, db: Session = Depends(get_db)):
    invoices = db.query(SaleInvoice).order_by(SaleInvoice.created_at.desc()).limit(50).all()
    return templates.TemplateResponse(request, "sales.html", {
        "invoices": invoices,
        "page": "sales"
    })


@app.get("/sales/new", response_class=HTMLResponse)
def new_sale(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.is_active == True, Product.stock_qty > 0).order_by(Product.name).all()
    customers = db.query(Customer).order_by(Customer.name).all()
    return templates.TemplateResponse(request, "sale_new.html", {
        "products": products,
        "customers": customers,
        "page": "sales"
    })


@app.post("/sales/create")
async def create_sale(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    customer_id = form.get("customer_id") or None
    if customer_id:
        customer_id = int(customer_id)

    # إنشاء رقم فاتورة
    last = db.query(SaleInvoice).order_by(SaleInvoice.id.desc()).first()
    inv_num = f"S-{datetime.now().strftime('%Y%m%d')}-{(last.id + 1) if last else 1:04d}"

    invoice = SaleInvoice(
        invoice_number=inv_num,
        customer_id=customer_id,
        payment_method=form.get("payment_method", "نقدي"),
        notes=form.get("notes", "")
    )
    db.add(invoice)
    db.flush()

    total = 0
    # المنتجات المختارة
    product_ids = form.getlist("product_id")
    quantities = form.getlist("quantity")
    prices = form.getlist("unit_price")

    for pid, qty, price in zip(product_ids, quantities, prices):
        if not pid or not qty:
            continue
        pid, qty, price = int(pid), float(qty), float(price)
        product = db.query(Product).get(pid)
        if not product or product.stock_qty < qty:
            continue

        item_total = qty * price
        total += item_total

        item = SaleItem(
            invoice_id=invoice.id,
            product_id=pid,
            quantity=qty,
            unit_price=price,
            total=item_total
        )
        db.add(item)

        # خصم من المخزون
        product.stock_qty -= qty
        movement = StockMovement(
            product_id=pid,
            movement_type="out",
            quantity=-qty,
            reference=inv_num,
            notes="بيع"
        )
        db.add(movement)

    invoice.total_amount = total
    payment = form.get("payment_method", "نقدي")
    if payment == "آجل" and customer_id:
        invoice.paid_amount = 0
        customer = db.query(Customer).get(customer_id)
        if customer:
            customer.balance = (customer.balance or 0) + total
    else:
        invoice.paid_amount = total
    db.commit()
    return RedirectResponse(f"/sales", status_code=303)


# ==================== التقارير ====================

@app.get("/reports", response_class=HTMLResponse)
def reports(request: Request, db: Session = Depends(get_db)):
    low_stock = db.query(Product).filter(
        Product.stock_qty <= Product.min_stock,
        Product.is_active == True
    ).order_by(Product.stock_qty).all()

    # أعلى المنتجات مبيعاً (تقريبي)
    from sqlalchemy import func
    top_products = db.query(
        Product.name,
        func.sum(SaleItem.quantity).label("total_qty")
    ).join(SaleItem).group_by(Product.id).order_by(func.sum(SaleItem.quantity).desc()).limit(10).all()

    return templates.TemplateResponse(request, "reports.html", {
        "low_stock": low_stock,
        "top_products": top_products,
        "page": "reports"
    })


# ==================== المشتريات ====================

@app.get("/purchases", response_class=HTMLResponse)
def purchases_list(request: Request, db: Session = Depends(get_db)):
    invoices = db.query(PurchaseInvoice).order_by(PurchaseInvoice.created_at.desc()).limit(50).all()
    return templates.TemplateResponse(request, "purchases.html", {
        "invoices": invoices,
        "page": "purchases"
    })


@app.get("/purchases/new", response_class=HTMLResponse)
def new_purchase(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.is_active == True).order_by(Product.name).all()
    suppliers = db.query(Supplier).order_by(Supplier.name).all()
    return templates.TemplateResponse(request, "purchase_new.html", {
        "products": products,
        "suppliers": suppliers,
        "page": "purchases"
    })


@app.post("/purchases/create")
async def create_purchase(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    supplier_id = form.get("supplier_id") or None
    if supplier_id:
        supplier_id = int(supplier_id)

    last = db.query(PurchaseInvoice).order_by(PurchaseInvoice.id.desc()).first()
    inv_num = f"P-{datetime.now().strftime('%Y%m%d')}-{(last.id + 1) if last else 1:04d}"

    invoice = PurchaseInvoice(
        invoice_number=inv_num,
        supplier_id=supplier_id,
        notes=form.get("notes", "")
    )
    db.add(invoice)
    db.flush()

    total = 0
    product_ids = form.getlist("product_id")
    quantities = form.getlist("quantity")
    costs = form.getlist("unit_cost")

    for pid, qty, cost in zip(product_ids, quantities, costs):
        if not pid or not qty:
            continue
        pid, qty, cost = int(pid), float(qty), float(cost)
        product = db.query(Product).get(pid)
        if not product:
            continue

        item_total = qty * cost
        total += item_total

        item = PurchaseItem(
            invoice_id=invoice.id,
            product_id=pid,
            quantity=qty,
            unit_cost=cost,
            total=item_total
        )
        db.add(item)

        # زيادة المخزون
        product.stock_qty += qty
        if cost > 0:
            product.cost_price = cost  # تحديث سعر التكلفة

        movement = StockMovement(
            product_id=pid,
            movement_type="in",
            quantity=qty,
            reference=inv_num,
            notes="شراء"
        )
        db.add(movement)

    invoice.total_amount = total
    db.commit()
    return RedirectResponse("/purchases", status_code=303)


# ==================== عرض فاتورة مبيعات ====================

@app.get("/sales/{invoice_id}", response_class=HTMLResponse)
def view_sale(invoice_id: int, request: Request, db: Session = Depends(get_db)):
    invoice = db.query(SaleInvoice).get(invoice_id)
    if not invoice:
        raise HTTPException(404, "الفاتورة غير موجودة")
    return templates.TemplateResponse(request, "sale_view.html", {
        "invoice": invoice,
        "page": "sales"
    })
