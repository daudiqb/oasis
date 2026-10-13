import { useState } from 'react'
import { createListing } from './api'

const CATEGORIES = ['books', 'electronics', 'furniture', 'clothing', 'home', 'other']
const CONDITIONS = ['new', 'like new', 'good', 'fair', 'worn']

const initialForm = {
  seller_id: '',
  title: '',
  description: '',
  price: '',
  category: '',
  item_condition: '',
}

function CreateListingForm({ onCreated }) {
  const [form, setForm] = useState(initialForm)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  function updateField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)

    const price = Number(form.price)
    if (!form.seller_id || !form.title || form.price === '' || Number.isNaN(price) || price < 0) {
      setError('Seller ID, title, and a non-negative price are required.')
      return
    }

    setSubmitting(true)
    try {
      const listing = await createListing({
        seller_id: Number(form.seller_id),
        title: form.title,
        description: form.description || undefined,
        price,
        category: form.category || undefined,
        item_condition: form.item_condition || undefined,
      })
      setForm(initialForm)
      onCreated(listing)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="create-listing-form" onSubmit={handleSubmit}>
      <h2>List an item</h2>

      <label>
        Your user ID
        <input
          type="number"
          min="1"
          value={form.seller_id}
          onChange={(e) => updateField('seller_id', e.target.value)}
          placeholder="e.g. 1 (no login yet)"
          required
        />
      </label>

      <label>
        Title
        <input
          type="text"
          value={form.title}
          onChange={(e) => updateField('title', e.target.value)}
          required
        />
      </label>

      <label>
        Description
        <textarea
          value={form.description}
          onChange={(e) => updateField('description', e.target.value)}
          rows={3}
        />
      </label>

      <div className="form-row">
        <label>
          Price ($)
          <input
            type="number"
            min="0"
            step="0.01"
            value={form.price}
            onChange={(e) => updateField('price', e.target.value)}
            required
          />
        </label>

        <label>
          Category
          <select value={form.category} onChange={(e) => updateField('category', e.target.value)}>
            <option value="">Select...</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>

        <label>
          Condition
          <select
            value={form.item_condition}
            onChange={(e) => updateField('item_condition', e.target.value)}
          >
            <option value="">Select...</option>
            {CONDITIONS.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error && <p className="state-message state-error">{error}</p>}

      <button type="submit" disabled={submitting}>
        {submitting ? 'Posting…' : 'Post listing'}
      </button>
    </form>
  )
}

export default CreateListingForm
