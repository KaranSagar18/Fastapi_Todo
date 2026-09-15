from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import select
from passlib.context import CryptContext

from database import SessionLocal, engine, Base
from models import User, Task

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
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
    user_exists = db.scalar(check)
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
    exists = db.scalar(stmt)
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
    response.set_cookie(
        key="user_id",
        value= str(exists.id),
        httponly=True
    )
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("user_id")
    return response

@app.get("/", response_class=HTMLResponse)
def read_index(request : Request , db : Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    user = None
    tasks = []

    if user_id:
        user_id = int(user_id)
        stmt = select(User).where(User.id == user_id)
        user = db.scalar(stmt)
        if user:
            tasks = db.scalars(select(Task).where(Task.owner_id == user_id)).all()

    return templates.TemplateResponse(
        request= request,
        name="index.html",
        context={"tasks" : tasks , "user" : user}
    )

@app.post("/tasks")
def add_task(
    request : Request,
    title : str = Form(...),
    db : Session = Depends(get_db)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login",status_code=303)
    task = Task(title = title , owner_id = int(user_id))
    db.add(task)
    db.commit()
    return RedirectResponse(url="/",status_code=303)

@app.post('/tasks/{task_id}/toggle')
def toggle_task(
    task_id : int,
    request : Request,
    db : Session = Depends(get_db)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login",status_code=303)

    user_id = int(user_id)
    stmt = select(Task).where(Task.id == task_id, Task.owner_id == user_id)
    task = db.scalar(stmt)
    if not task:
        raise HTTPException(
            status_code=404, 
            detail="Task Not Found"
        )
    task.completed = not task.completed
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/tasks/{task_id}/delete")
def delete_task(
    task_id : int,
    request : Request,
    db : Session = Depends(get_db)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    user_id = int(user_id)
    stmt = select(Task).where(Task.id == task_id , Task.owner_id == user_id)
    task = db.scalar(stmt)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/tasks/{task_id}/update")
def update_task(
    task_id : int,
    request : Request,
    title : str = Form(...),
    db : Session = Depends(get_db)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    user_id = int(user_id)
    stmt = select(Task).where(Task.id == task_id, Task.owner_id == user_id)
    task = db.scalar(stmt)

    if not task:
        raise HTTPException(status_code=404, detail="Task Not Found")

    task.title = title
    db.commit()
    return RedirectResponse(url='/', status_code=303)

@app.get("/add-task", response_class= HTMLResponse)
def add_task_page(
    request : Request,
    db : Session = Depends(get_db)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login",status_code=303)

    user_id = int(user_id)
    stmt = select(User).where(User.id == user_id)
    user = db.scalar(stmt)
    if not user:
        return RedirectResponse(url="/login",status_code=303)
    return templates.TemplateResponse(
        request= request,
        name="add_task.html",
        context= {"user" : user}
    )