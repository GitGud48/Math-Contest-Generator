'use client'

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import ProblemCard from '../components/ProblemCard'
import Link from 'next/link'

interface SearchResult {
  id: number
  statement: string
  solution?: string
  source: 'imo' | 'putnam' | 'mit'
  problem_label?: string
  category?: string
}

function SearchResults() {
  const searchParams = useSearchParams()
  const query = searchParams.get('q') || ''
  
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function performSearch() {
      if (!query || query.length < 2) {
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        setError(null)
        
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`)
        const data = await response.json()
        
        if (!response.ok) {
          throw new Error(data.error || 'Search failed')
        }
        
        setResults(data.results || [])
      } catch (err: any) {
        console.error('Search error:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    performSearch()
  }, [query])

  if (loading) {
    return (
      <div className="search-loading">
        <div className="loading-spinner"></div>
        <p>Searching across all databases...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-message">
        <h3>Search Error</h3>
        <p>{error}</p>
        <Link href="/" className="back-link">← Back to Home</Link>
      </div>
    )
  }

  return (
    <div className="search-results-container">
      <div className="search-header">
        <Link href="/" className="back-link">← Back to Home</Link>
        <h2>Search Results for "{query}"</h2>
        <p className="results-count">
          Found {results.length} problem{results.length !== 1 ? 's' : ''}
        </p>
      </div>

      {results.length === 0 ? (
        <div className="no-results">
          <p>No problems found matching your search.</p>
          <p>Try different keywords or browse problems by category.</p>
        </div>
      ) : (
        <div className="problems-grid">
          {results.map((problem, index) => (
            <ProblemCard 
              key={`${problem.source}-${problem.id}`}
              problem={problem as any}
              source={problem.source}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <SearchResults />
    </Suspense>
  )
}
