from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import SessionLocal, engine, get_db
import models, schemas
from sqlalchemy import func
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Library API",
    description="REST API для учёта книг в библиотеке",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Создание книги
@app.post("/books/", response_model=schemas.BookResponse, status_code=201)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    db_book = models.Book(**book.model_dump() if hasattr(book, 'model_dump') else book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

# 2. Получение списка книг с фильтрацией, пагинацией и сортировкой
@app.get("/books/", response_model=List[schemas.BookResponse])
def get_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
    author: Optional[str] = None,
    genre: Optional[str] = None,
    sort_by: str = Query("id", pattern="^(id|title|year|price)$"),
    db: Session = Depends(get_db)
):
    query = db.query(models.Book)
    
    if author:
        query = query.filter(models.Book.author.ilike(f"%{author}%"))
    if genre:
        query = query.filter(models.Book.genre.ilike(f"%{genre}%"))
        
    order_column = getattr(models.Book, sort_by)
    books = query.order_by(order_column).offset(skip).limit(limit).all()
    return books

# 3. Получение книги по ID
@app.get("/books/{book_id}", response_model=schemas.BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

# 4. Обновление книги
@app.put("/books/{book_id}", response_model=schemas.BookResponse)
def update_book(book_id: int, book_update: schemas.BookUpdate, db: Session = Depends(get_db)):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
        
    update_data = book_update.model_dump(exclude_unset=True) if hasattr(book_update, 'model_dump') else book_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_book, key, value)
        
    db.commit()
    db.refresh(db_book)
    return db_book

# 5. Удаление книги
@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
        
    db.delete(db_book)
    db.commit()
    return

# 6. Агрегация: количество книг по жанрам
@app.get("/stats/genre-counts")
def get_genre_counts(db: Session = Depends(get_db)):
    counts = db.query(models.Book.genre, func.count(models.Book.id)).group_by(models.Book.genre).all()
    return [{"genre": c[0], "count": c[1]} for c in counts]

# 7. Изменение статуса: взять книгу
@app.post("/books/{book_id}/borrow")
def borrow_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    if not db_book.is_available:
        raise HTTPException(status_code=400, detail="Book is already borrowed")
        
    db_book.is_available = False
    db.commit()
    return {"detail": "Book borrowed successfully"}
