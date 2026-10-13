import { useEffect, useState } from 'react'
import './App.css'
import { getListings } from './api'
import CreateListingForm from './CreateListingForm'

const CATEGORIES = ['books', 'electronics', 'furniture', 'clothing', 'home', 'other']
const STATUSES = ['available', 'pending', 'sold']

function formatPrice(price) {
  return `$${Number(price).toFixed(2)}`
}

function ListingCard({ listing }) {
  return (
    <li className="listing-card">
      <div className="listing-card-top">
        <h3>{listing.title}</h3>
        <span className={`status-badge status-${listing.status}`}>{listing.status}</span>
      </div>
      <p className="listing-price">{formatPrice(listing.price)}</p>
      {listing.description && <p className="listing-description">{listing.description}</p>}
      <div className="listing-meta">
        {listing.category && <span className="tag">{listing.category}</span>}
        {listing.item_condition && <span className="tag">{listing.item_condition}</span>}
      </div>
    </li>
  )
}

function App() {
  const [listings, setListings] = useState([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    getListings({ search, category, status })
      .then((data) => {
        if (active) setListings(data)
      })
      .catch((err) => {
        if (active) setError(err.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [search, category, status])

  return (
    <>
      <header className="app-header">
        <h1>Campus Marketplace</h1>
        <p>Browse items other students are selling</p>
        <button
          type="button"
          className="toggle-form-button"
          onClick={() => setShowForm((prev) => !prev)}
        >
          {showForm ? 'Cancel' : '+ List an item'}
        </button>
      </header>

      {showForm && (
        <CreateListingForm
          onCreated={(listing) => {
            setListings((prev) => [listing, ...prev])
            setShowForm(false)
          }}
        />
      )}

      <section className="filters">
        <input
          type="search"
          placeholder="Search listings..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">All categories</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </section>

      <section className="listings-section">
        {loading && <p className="state-message">Loading listings…</p>}
        {error && <p className="state-message state-error">Couldn't load listings: {error}</p>}
        {!loading && !error && listings.length === 0 && (
          <p className="state-message">No listings match your search.</p>
        )}
        {!loading && !error && listings.length > 0 && (
          <ul className="listings-grid">
            {listings.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </ul>
        )}
      </section>
    </>
  )
}

export default App
