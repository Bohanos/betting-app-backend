import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic_settings import BaseSettings

# Local imports
import models
import schemas
import auth
from database import engine, get_db

# 1. Configuration (Reads from .env or Environment Variables)
class Settings(BaseSettings):
    secret_key: str = "supersecretdefaultkey"  # Change this for production!
    database_url: str = "sqlite:///./app.db"
    
    class Config:
        env_file = ".env"

settings = Settings()

# 2. Initialize Database Tables
models.Base.metadata.create_all(bind=engine)

# 3. FastAPI Application Instance
app = FastAPI(
    title="BetBook API",
    description="Backend for managing bet bookings",
    version="1.0.0"
)

# ── Health Check ─────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "BetBook API is operational"}

# ── Authentication ───────────────────────────────────────────
@app.post("/auth/register", response_model=schemas.UserOut, tags=["Auth"])
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user = models.User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=auth.hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/auth/login", response_model=schemas.Token, tags=["Auth"])
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form.username).first()
    if not user or not auth.verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Use the settings.secret_key here if your auth module supports it
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ── Games Operations ─────────────────────────────────────────

@app.post("/games", response_model=schemas.GameOut, tags=["Games"])
def create_game(game_in: schemas.GameCreate, db: Session = Depends(get_db)):
    new_game = models.Game(title=game_in.title)
    db.add(new_game)
    db.commit()
    db.refresh(new_game)
    return new_game

@app.get("/games/{game_id}", response_model=schemas.GameOut, tags=["Games"])
def get_game(game_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

@app.post("/games/{game_id}/book", response_model=schemas.GameOut, tags=["Games"])
def book_game(game_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.is_booked:
        raise HTTPException(status_code=400, detail="Game already booked")
    
    game.is_booked = True
    game.user_id = current_user.id
    db.commit()
    db.refresh(game)
    return game

@app.delete("/games/{game_id}", tags=["Games"])
def delete_game(game_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    db.delete(game)
    db.commit()
    return {"detail": "Game deleted successfully"}