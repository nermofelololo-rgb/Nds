# نيو دنت NDS - نظام المحاسبة والمخزون

## طريقة التشغيل المحلي
```bash
pip install -r requirements.txt
python run.py
```
ثم افتح: http://127.0.0.1:8000

## بيانات الدخول
| المستخدم | كلمة المرور | النوع |
|----------|-------------|-------|
| admin    | admin123    | مدير  |
| clinic1  | clinic123   | عميل  |

## رفع البرنامج على Render (مجاني)

### 1. ارفع الكود على GitHub
- اعمل حساب على github.com
- اعمل Repository جديد اسمه مثلاً `nds-accounting`
- ارفع كل الملفات الموجودة في هذا المجلد

### 2. اعمل حساب على Render
- ادخل على: https://render.com
- سجّل بحساب جوجل

### 3. أنشئ Web Service
1. New + → Web Service
2. اربط GitHub واختار المشروع
3. الإعدادات:
   - Name: nds-accounting
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python run.py`
4. اضغط Create Web Service

### 4. بعد ما يخلص
هيديك لينك زي: https://nds-accounting.onrender.com

### 5. اعمل Shortcut على الموبايل
- أندرويد (كروم): ⋮ → إضافة إلى الشاشة الرئيسية
- آيفون (سفاري): مشاركة → إضافة إلى الشاشة الرئيسية

## ملاحظات
- الاستضافة المجانية قد تمسح البيانات لو البرنامج نام فترة طويلة
- غيّر كلمة مرور admin بعد أول دخول
