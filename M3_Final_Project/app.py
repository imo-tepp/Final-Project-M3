from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from prometheus_fastapi_instrumentator import Instrumentator
import os

# SQLAlchemy setup
DATABASE_URL = "sqlite:///./banking.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing setup
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# FastAPI setup
app = FastAPI()
# Dynamically determine the path to the templates directory
current_file_directory = os.path.dirname(__file__)
templates_directory = os.path.join(current_file_directory, "templates")

# Initialize Jinja2Templates with the relative path
templates = Jinja2Templates(directory=templates_directory)

# Initialize the Instrumentator for Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# SQLAlchemy models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=False)
    password = Column(String(150), nullable=False)
    balance = Column(Float, default=0.0)

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility functions
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    hashed_password = get_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login failed!")
    return JSONResponse(content={"message": "Login successful!"})

@app.post("/deposit")
def deposit(username: str = Form(...), password: str = Form(...), amount: float = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.password):
        user.balance += amount
        db.commit()
        db.refresh(user)
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Transaction failed!")

@app.post("/withdraw")
def withdraw(username: str = Form(...), password: str = Form(...), amount: float = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.password):
        if user.balance >= amount:
            user.balance -= amount
            db.commit()
            db.refresh(user)
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds!")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Transaction failed!")

@app.post("/balance")
def balance(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.password):
        return JSONResponse(content={"balance": user.balance})
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to retrieve balance!")

@app.get("/view_users")
def view_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    user_data = [{"id": user.id, "username": user.username, "balance": user.balance} for user in users]
    return JSONResponse(content=user_data)

# Create the database tables
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)