import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(true)
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
    <div className="App">
      <h1>Library Manager</h1>
      
      <div className="add-book-form">
        <h2>Add a New Book</h2>
        <form onSubmit={handleSubmit}>
          <input type="text" name="title" placeholder="Title" value={newBook.title} onChange={handleInputChange} required />
          <input type="text" name="author" placeholder="Author" value={newBook.author} onChange={handleInputChange} required />
          <input type="text" name="genre" placeholder="Genre" value={newBook.genre} onChange={handleInputChange} required />
          <input type="number" name="year" placeholder="Year" value={newBook.year} onChange={handleInputChange} required />
          <input type="number" step="0.01" name="price" placeholder="Price" value={newBook.price} onChange={handleInputChange} required />
          <button type="submit">Add Book</button>
        </form>
      </div>

      <div className="books-list">
        <h2>Books List</h2>
        {loading ? <p>Loading...</p> : (
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Author</th>
                <th>Genre</th>
                <th>Year</th>
                <th>Price</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {books.map(book => (
                <tr key={book.id}>
                  <td>{book.title}</td>
                  <td>{book.author}</td>
                  <td>{book.genre}</td>
                  <td>{book.year}</td>
                  <td>${book.price}</td>
                  <td>
                    <button onClick={() => deleteBook(book.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

export default App
