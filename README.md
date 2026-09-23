# Inventory Management App

A ready-to-run Django inventory app using SQLite (no MySQL setup required).

## Features
- Dashboard
- Products
- Categories
- Stock in / stock out
- Low-stock indicator
- Search products
- Automatic stock updates
- Admin panel

## Windows setup

```powershell
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
py manage.py migrate
py manage.py createsuperuser
py manage.py runserver
```

Open:
- App: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## PowerShell npm issue
This project does NOT require Node/npm.
