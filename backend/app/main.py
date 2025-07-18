from fastapi import FastAPI, Depends, HTTPException, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import os

from .database import engine, get_db
from .models import Base, User, CountEntry, Settings
from .auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, get_admin_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from .utils import generate_qr_code, generate_payment_qr

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Beer Counter")

# Mount static files and templates
static_dir = "/app/frontend/static"
templates_dir = "/app/frontend/templates"

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=templates_dir)

# Create default admin user
def create_default_admin():
    db = next(get_db())
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin"),
            is_admin=True
        )
        db.add(admin)
        db.commit()
    db.close()

create_default_admin()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if user exists
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password)
    )
    db.add(user)
    db.commit()
    
    return RedirectResponse(url="/login", status_code=302)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user
    })

@app.post("/add-count")
async def add_count(
    amount: int = Form(1),
    entry_type: str = Form("beer"),
    note: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = CountEntry(
        user_id=current_user.id,
        amount=amount,
        entry_type=entry_type,
        note=note if note else None
    )
    db.add(entry)
    
    # Update user counts based on type
    if entry_type == "beer":
        current_user.count += amount
    elif entry_type == "birell":
        current_user.birell_count += amount
    elif entry_type == "entry":
        current_user.entry_count += amount
    
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/calculate-payment/{user_id}")
async def calculate_payment(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only allow users to see their own payment or admins
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = db.query(User).filter(User.id == user_id).first()
    settings = db.query(Settings).first()
    if not settings:
        settings = Settings()
        db.add(settings)
        db.commit()
    
    # Calculate totals
    beer_total = user.count * settings.beer_price
    birell_total = user.birell_count * settings.birell_price
    entry_total = user.entry_count * settings.entry_price
    
    # Generate payment QR codes
    drinks_total = beer_total + birell_total
    drinks_qr = None
    entry_qr = None
    
    if drinks_total > 0:
        drinks_qr = generate_payment_qr(drinks_total, f"Piva a birelly - {user.username}", settings.payment_account)
    
    if entry_total > 0:
        entry_qr = generate_payment_qr(entry_total, f"Vstupne - {user.username}", settings.payment_account)
    
    return templates.TemplateResponse("payment.html", {
        "request": request,
        "user": user,
        "settings": settings,
        "beer_total": beer_total,
        "birell_total": birell_total,
        "entry_total": entry_total,
        "drinks_total": drinks_total,
        "drinks_qr": drinks_qr,
        "entry_qr": entry_qr
    })

@app.get("/qr/{user_id}", response_class=HTMLResponse)
async def user_qr(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate QR code with registration/login URL
    base_url = str(request.base_url).rstrip('/')
    qr_url = f"{base_url}/register?ref={user.username}"
    qr_code = generate_qr_code(qr_url)
    
    return templates.TemplateResponse("qr.html", {
        "request": request,
        "user": user,
        "qr_code": qr_code,
        "qr_url": qr_url
    })

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(
    request: Request,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    total_count = sum(user.count for user in users)
    settings = db.query(Settings).first()
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "users": users,
        "total_count": total_count,
        "settings": settings
    })

@app.post("/admin/reset-user/{user_id}")
async def reset_user_count(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.count = 0
        user.birell_count = 0
        user.entry_count = 0
        # Delete all entries
        db.query(CountEntry).filter(CountEntry.user_id == user_id).delete()
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=302)

@app.post("/admin/reset-password/{user_id}")
async def reset_user_password(
    user_id: int,
    new_password: str = Form(...),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.hashed_password = get_password_hash(new_password)
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=302)

@app.post("/admin/delete-user/{user_id}")
async def delete_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if user and not user.is_admin:
        db.query(CountEntry).filter(CountEntry.user_id == user_id).delete()
        db.delete(user)
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=302)

@app.post("/admin/settings")
async def update_settings(
    beer_price: float = Form(...),
    birell_price: float = Form(...),
    entry_price: float = Form(...),
    payment_account: str = Form(...),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    settings = db.query(Settings).first()
    if not settings:
        settings = Settings()
        db.add(settings)
    
    settings.beer_price = beer_price
    settings.birell_price = birell_price
    settings.entry_price = entry_price
    settings.payment_account = payment_account
    db.commit()
    
    return RedirectResponse(url="/admin", status_code=302)

@app.post("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(key="access_token")
    return response