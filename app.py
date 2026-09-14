from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database import SessionLocal, engine, Base
from models import User, Task

Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated = "auto"
)

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally: 
        db.close()

@app.get("/register", response_class= HTMLResponse)
def register_page(request : Request):

    return templates.TemplateResponse(
        request = request,
        name = "register.html" 
    )

@app.post("/register")
def register(
    request : Request,
    username : str = Form(...), # ... means the value is required
    password : str = Form(...),
    db : Session = Depends(get_db)
):
    check = select(User).where(User.username == username)
    user_exists = db.scalars(check).one_or_none()
    if user_exists:
        return templates.TemplateResponse(
            request=request, 
            name="register.html", 
            context={"error": "Username already exists"}
        )
    hashed_password = pwd_context.hash(password)
    user = User(username = username, hashed_password = hashed_password)
    db.add(user)
    db.commit()
    return RedirectResponse(url="/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def login_page(request : Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )

@app.post("/login")
def login(
    request : Request,
    username : str = Form(...),
    password : str = Form(...),
    db : Session = Depends(get_db)
):
    stmt = select(User).where(User.username == username)
    exists = db.scalars(stmt).one_or_none()

    if not exists:
        return templates.TemplateResponse(
            request= request,
            name= "login.html",
            context={"error" : "User not found!"}
        )
    if not pwd_context.verify(password , exists.hashed_password):
        return templates.TemplateResponse(
            request= request,
            name= "login.html",
            context={"error" : "Password is incorrect!"}
        )
    response = RedirectResponse(url="/",status_code= 303)
    response.set_cookie(key="user_id",value= str(exists.id),httponly=True)
    return response