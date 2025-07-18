from fastapi import FastAPI, Depends, HTTPException, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import os
from pathlib import Path

from .database import engine, get_db
from .models import Base, User, CountEntry
from .auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, get_admin_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from .utils import generate_qr_code

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Beer Counter")

# Mount static files and templates with existence check
static_dir = "/app/frontend/static"
templates_dir = "/app/frontend/templates"

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    print(f"Warning: Static directory {static_dir} not found")

if os.path.exists(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
else:
    # Create empty templates directory as fallback
    Path(templates_dir).mkdir(parents=True, exist_ok=True)
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
    response.set_cookie(key="token", value=access_token, httponly=True)
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
    recent_entries = db.query(CountEntry).filter(
        CountEntry.user_id == current_user.id
    ).order_by(CountEntry.timestamp.desc()).limit(10).all()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "recent_entries": recent_entries
    })

@app.post("/add-count")
async def add_count(
    amount: int = Form(1),
    note: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = CountEntry(
        user_id=current_user.id,
        amount=amount,
        note=note if note else None
    )
    db.add(entry)
    
    # Update user total count
    current_user.count += amount
    db.commit()
    
    return RedirectResponse(url="/dashboard", status_code=302)

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
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "users": users,
        "total_count": total_count
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
        # Delete all entries
        db.query(CountEntry).filter(CountEntry.user_id == user_id).delete()
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=302)

@app.post("/admin/delete-user/{user_id}")
async def delete_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if user and not user.is_admin:  # Don't delete admin users
        db.query(CountEntry).filter(CountEntry.user_id == user_id).delete()
        db.delete(user)
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=302)

@app.post("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(key="token")
    return response



