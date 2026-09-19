import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [newBook, setNewBook] = useState({
    title: '', author: '', genre: '', year: '', price: ''
  })
  
  const API_URL = 'http://localhost:8000/books/'

  useEffect(() => {
    fetchBooks()
  }, [])

  const fetchBooks = async () => {
    try {
      const response = await fetch(API_URL)
      const data = await response.json()
      setBooks(data)
    } catch (error) {
      console.error('Error fetching books:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setNewBook(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const bookToCreate = {
        ...newBook,
        year: parseInt(newBook.year),
        price: parseFloat(newBook.price)
      }
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bookToCreate)
      })
      if (response.ok) {
        setNewBook({ title: '', author: '', genre: '', year: '', price: '' })
        setIsModalOpen(false)
        fetchBooks()
      }
    } catch (error) {
      console.error('Error creating book:', error)
    }
  }

  const deleteBook = async (id) => {
    try {
      const response = await fetch(`${API_URL}${id}`, {
        method: 'DELETE'
      })
      if (response.ok) {
        fetchBooks()
      }
    } catch (error) {
      console.error('Error deleting book:', error)
    }
  }

  return (
    <div className="app-container">
      <header className="header">
        <div className="logo">📚 LibraryOS</div>
        <button className="add-btn" onClick={() => setIsModalOpen(true)}>
          + Add Book
        </button>
      </header>

      <main className="main-content">
        <div className="header-section">
          <h2>All Books</h2>
          <p className="subtitle">Manage your library collection</p>
        </div>

        {loading ? (
          <div className="loading">Loading books...</div>
        ) : (
          <div className="books-grid">
            {books.length === 0 ? (
              <div className="empty-state">No books in the library yet.</div>
            ) : (
              books.map(book => (
                <div className="book-card" key={book.id}>
                  <div className="book-card-header">
                    <span className="genre-badge">{book.genre}</span>
                    <span className="price-tag">${book.price}</span>
                  </div>
                  <h3 className="book-title">{book.title}</h3>
                  <p className="book-author">by {book.author}</p>
                  <div className="book-footer">
                    <span className="book-year">{book.year}</span>
                    <button className="delete-btn" onClick={() => deleteBook(book.id)}>
                      Remove
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </main>

      {isModalOpen && (
        <div className="modal-overlay" onClick={() => setIsModalOpen(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Add New Book</h2>
              <button className="close-btn" onClick={() => setIsModalOpen(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit} className="book-form">
              <div className="form-group">
                <label>Title</label>
                <input type="text" name="title" value={newBook.title} onChange={handleInputChange} required />
              </div>
              <div className="form-group">
                <label>Author</label>
                <input type="text" name="author" value={newBook.author} onChange={handleInputChange} required />
              </div>
              <div className="form-group-row">
                <div className="form-group">
                  <label>Genre</label>
                  <input type="text" name="genre" value={newBook.genre} onChange={handleInputChange} required />
                </div>
                <div className="form-group">
                  <label>Year</label>
                  <input type="number" name="year" value={newBook.year} onChange={handleInputChange} required />
                </div>
              </div>
              <div className="form-group">
                <label>Price ($)</label>
                <input type="number" step="0.01" name="price" value={newBook.price} onChange={handleInputChange} required />
              </div>
              <div className="form-actions">
                <button type="button" className="cancel-btn" onClick={() => setIsModalOpen(false)}>Cancel</button>
                <button type="submit" className="submit-btn">Save Book</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
