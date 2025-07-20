from fastapi import FastAPI, Depends, HTTPException, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import timedelta, datetime
import os
import io

from .database import engine, get_db
from .models import Base, User, CountEntry, Settings, Article, UserArticleCount
from .auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, get_admin_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from .utils import generate_qr_code, generate_payment_qr
from .pdf_utils import generate_user_report_pdf, generate_admin_summary_pdf
from .pdf_utils_weasy import generate_user_report_pdf_weasy

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

def create_default_articles():
    db = next(get_db())
    if db.query(Article).count() == 0:
        articles = [
            Article(name="Pivo", price=50.0, emoji="🍺", payment_account="123456789/0100"),
            Article(name="Birell", price=30.0, emoji="🥤", payment_account="123456789/0100"),
            Article(name="Vstupné", price=100.0, emoji="🎫", payment_account="987654321/0100"),
        ]
        for article in articles:
            db.add(article)
        db.commit()
    db.close()

@app.on_event("startup")
async def startup_event():
    create_default_admin()
    create_default_articles()

create_default_admin()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("error.html", {
            "request": request,
            "title": "Neplatné přihlašovací údaje",
            "emoji": "🔐",
            "message": "Špatné uživatelské jméno nebo heslo",
            "detail": "Zkontrolujte prosím své přihlašovací údaje a zkuste to znovu.",
            "show_login": True
        })
    
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
    # Získej aktivní články
    active_articles = db.query(Article).filter(Article.is_active == True).all()
    
    # Získej nebo vytvoř počty pro uživatele
    user_counts = []
    for article in active_articles:
        count = db.query(UserArticleCount).filter(
            UserArticleCount.user_id == current_user.id,
            UserArticleCount.article_id == article.id
        ).first()
        
        if not count:
            count = UserArticleCount(
                user_id=current_user.id,
                article_id=article.id,
                count=0
            )
            db.add(count)
            db.commit()
            db.refresh(count)
        
        count.article = article  # Přidej článek pro template
        user_counts.append(count)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "user_counts": user_counts  # Změněno z user_article_counts
    })

@app.post("/add-count")
async def add_count(
    article_id: int = Form(...),
    amount: int = Form(1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Najdi nebo vytvoř počet pro uživatele a článek
    count = db.query(UserArticleCount).filter(
        UserArticleCount.user_id == current_user.id,
        UserArticleCount.article_id == article_id
    ).first()
    
    if not count:
        count = UserArticleCount(
            user_id=current_user.id,
            article_id=article_id,
            count=0
        )
        db.add(count)
    
    count.count += amount
    if count.count < 0:
        count.count = 0
    
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/calculate-payment/{user_id}", response_class=HTMLResponse)
async def calculate_payment(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Seskup podle platebního účtu
    payment_groups = {}
    user_counts = db.query(UserArticleCount).join(Article).filter(
        UserArticleCount.user_id == user_id,
        UserArticleCount.count > 0
    ).all()
    
    print(f"Found {len(user_counts)} user counts for user {user_id}")  # Debug
    
    for count in user_counts:
        # Použij účet z článku, nebo výchozí
        account = count.article.payment_account
        if not account:
            account = "123456789/0100"  # Výchozí účet
            
        print(f"Processing article: {count.article.name}, account: {account}, count: {count.count}")  # Debug
            
        if account not in payment_groups:
            payment_groups[account] = {"total": 0, "items": []}
        
        total = count.count * count.article.price
        payment_groups[account]["total"] += total
        payment_groups[account]["items"].append({
            "name": count.article.name,
            "emoji": count.article.emoji,
            "count": count.count,
            "price": count.article.price,
            "total": total
        })
    
    print(f"Payment groups: {payment_groups}")  # Debug
    
    # Generuj QR kódy pro každý účet
    qr_codes = {}
    for account, data in payment_groups.items():
        if data["total"] > 0:
            items_text = ", ".join([f"{item['count']}x {item['name']}" for item in data["items"]])
            message = f"{items_text} - {user.username}"
            print(f"Generating QR for account: {account}, amount: {data['total']}, message: {message}")  # Debug
            qr_codes[account] = generate_payment_qr(data["total"], message, account)
            print(f"QR code generated for {account}: {len(qr_codes[account])} chars")  # Debug
    
    print(f"QR codes: {list(qr_codes.keys())}")  # Debug
    
    return templates.TemplateResponse("payment.html", {
        "request": request,
        "user": user,
        "payment_groups": payment_groups,
        "qr_codes": qr_codes
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
    articles = db.query(Article).all()
    
    # Spočítej celkové počty z UserArticleCount tabulky
    total_beer_count = 0
    total_birell_count = 0
    total_entry_count = 0
    
    # Najdi články podle názvu
    beer_article = db.query(Article).filter(Article.name == "Pivo").first()
    birell_article = db.query(Article).filter(Article.name == "Birell").first()
    entry_article = db.query(Article).filter(Article.name == "Vstupné").first()
    
    if beer_article:
        total_beer_count = db.query(func.sum(UserArticleCount.count)).filter(
            UserArticleCount.article_id == beer_article.id
        ).scalar() or 0
    
    if birell_article:
        total_birell_count = db.query(func.sum(UserArticleCount.count)).filter(
            UserArticleCount.article_id == birell_article.id
        ).scalar() or 0
        
    if entry_article:
        total_entry_count = db.query(func.sum(UserArticleCount.count)).filter(
            UserArticleCount.article_id == entry_article.id
        ).scalar() or 0
    
    # Přidej počty článků k uživatelům
    for user in users:
        user.beer_count_new = 0
        user.birell_count_new = 0
        user.entry_count_new = 0
        
        if beer_article:
            count = db.query(UserArticleCount).filter(
                UserArticleCount.user_id == user.id,
                UserArticleCount.article_id == beer_article.id
            ).first()
            user.beer_count_new = count.count if count else 0
            
        if birell_article:
            count = db.query(UserArticleCount).filter(
                UserArticleCount.user_id == user.id,
                UserArticleCount.article_id == birell_article.id
            ).first()
            user.birell_count_new = count.count if count else 0
            
        if entry_article:
            count = db.query(UserArticleCount).filter(
                UserArticleCount.user_id == user.id,
                UserArticleCount.article_id == entry_article.id
            ).first()
            user.entry_count_new = count.count if count else 0
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "users": users,
        "articles": articles,
        "total_beer_count": total_beer_count,
        "total_birell_count": total_birell_count,
        "total_entry_count": total_entry_count
    })

@app.post("/admin/reset-user/{user_id}")
async def reset_user_count(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        # Delete all entries
        db.query(CountEntry).filter(CountEntry.user_id == user_id).delete()
        # Reset article counts
        db.query(UserArticleCount).filter(UserArticleCount.user_id == user_id).delete()
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
        db.query(UserArticleCount).filter(UserArticleCount.user_id == user_id).delete()
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

@app.post("/admin/toggle-admin/{user_id}")
async def toggle_admin(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.id != admin_user.id:  # Nemůže odebrat admin práva sobě
        user.is_admin = not user.is_admin
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=302)

@app.post("/admin/mark-paid/{user_id}")
async def mark_paid(
    user_id: int,
    article_ids: list[int] = Form(...),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    for article_id in article_ids:
        count = db.query(UserArticleCount).filter(
            UserArticleCount.user_id == user_id,
            UserArticleCount.article_id == article_id
        ).first()
        
        if count:
            count.count = 0  # Vynuluj počet = označit jako zaplaceno
    
    db.commit()
    return RedirectResponse(url="/admin", status_code=302)

@app.post("/admin/articles")
async def create_article(
    name: str = Form(...),
    price: float = Form(...),
    emoji: str = Form(...),
    payment_account: str = Form(...),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    article = Article(
        name=name,
        price=price,
        emoji=emoji,
        payment_account=payment_account,
        is_active=True
    )
    db.add(article)
    db.commit()
    
    return RedirectResponse(url="/admin", status_code=302)

@app.post("/admin/articles/{article_id}/delete")
async def delete_article(
    article_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if article:
        # Smaž všechny počty pro tento článek
        db.query(UserArticleCount).filter(UserArticleCount.article_id == article_id).delete()
        # Smaž článek
        db.delete(article)
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=302)

@app.post("/admin/articles/{article_id}/toggle")
async def toggle_article(
    article_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if article:
        article.is_active = not article.is_active
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=302)

@app.post("/admin/articles/{article_id}")
async def update_article(
    article_id: int,
    name: str = Form(...),
    price: float = Form(...),
    emoji: str = Form(...),
    payment_account: str = Form(...),
    is_active: bool = Form(False),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if article:
        article.name = name
        article.price = price
        article.emoji = emoji
        article.payment_account = payment_account
        article.is_active = is_active
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=302)

@app.post("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(key="access_token")
    return response

@app.get("/pdf/user/{user_id}")
async def download_user_pdf(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Uživatel může stáhnout pouze svůj PDF nebo admin může stáhnout jakýkoliv
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user counts
    user_counts = db.query(UserArticleCount).join(Article).filter(
        UserArticleCount.user_id == user_id,
        UserArticleCount.count > 0
    ).all()
    
    # Calculate total
    total_amount = sum(count.count * count.article.price for count in user_counts)
    
    # Generate PDF
    pdf_buffer = generate_user_report_pdf(user, user_counts, total_amount)
    
    return StreamingResponse(
        io.BytesIO(pdf_buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=rozuctovani_{user.username}.pdf"}
    )

@app.get("/pdf/admin/summary")
async def download_admin_summary(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    articles = db.query(Article).all()
    
    # Prepare data
    users_data = []
    for user in users:
        user_data = {'username': user.username}
        for article in articles:
            count = db.query(UserArticleCount).filter(
                UserArticleCount.user_id == user.id,
                UserArticleCount.article_id == article.id
            ).first()
            user_data[f'article_{article.id}'] = count.count if count else 0
        users_data.append(user_data)
    
    # Generate PDF
    pdf_buffer = generate_admin_summary_pdf(users_data, articles)
    
    return StreamingResponse(
        io.BytesIO(pdf_buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=celkovy_prehled.pdf"}
    )

@app.get("/pdf/user-weasy/{user_id}")
async def download_user_pdf_weasy(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Pouze admin nebo vlastní PDF
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_counts = db.query(UserArticleCount).join(Article).filter(
        UserArticleCount.user_id == user_id,
        UserArticleCount.count > 0
    ).all()
    
    total_amount = sum(count.count * count.article.price for count in user_counts)
    
    # Generate PDF with WeasyPrint
    pdf_buffer = generate_user_report_pdf_weasy(user, user_counts, total_amount)
    
    return StreamingResponse(
        io.BytesIO(pdf_buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=rozuctovani_{user.username}_weasy.pdf"}
    )

@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("error.html", {
        "request": request,
        "title": "Neautorizovaný přístup",
        "emoji": "🚫",
        "message": "Nejste přihlášeni nebo vypršela platnost přihlášení",
        "detail": "Pro pokračování se prosím přihlaste.",
        "show_login": True
    }, status_code=401)









