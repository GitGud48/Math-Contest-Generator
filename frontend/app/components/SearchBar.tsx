'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function SearchBar() {
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const router = useRouter()

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (query.trim().length < 2) {
      alert('Please enter at least 2 characters')
      return
    }

    setIsSearching(true)
    router.push(`/search?q=${encodeURIComponent(query)}`)
  }

  return (
    <form onSubmit={handleSearch} className="search-bar">
      <div className="search-container">
        <input
          type="text"
          placeholder="Search problems across all competitions..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="search-input"
          disabled={isSearching}
        />
        <button 
          type="submit" 
          className="search-button"
          disabled={isSearching || query.trim().length < 2}
        >
          {isSearching ? '🔍 Searching...' : '🔍 Search'}
        </button>
      </div>
      <p className="search-hint">
        Search by keywords, topics, or problem content
      </p>
    </form>
  )
}
