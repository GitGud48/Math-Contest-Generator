'use client'

import { useState } from 'react'
import DatabaseSelector from './components/DatabaseSelector'
import ProblemView from './components/ProblemView'
import SearchBar from './components/SearchBar'

type DatabaseSource = 'imo' | 'putnam' | 'mit'

export default function Home() {
  const [selectedSource, setSelectedSource] = useState<DatabaseSource | null>(null)

  const handleSourceSelect = (source: DatabaseSource) => {
    setSelectedSource(source)
  }

  const handleBackToSelection = () => {
    setSelectedSource(null)
  }

  return (
    <div className="container">
      <header className="page-header">
        <h1>Math Problem Generator</h1>
        <p>Generate and solve mathematical competition problems from IMO, Putnam, and MIT</p>
      </header>
      <SearchBar />

      {!selectedSource ? (
        <DatabaseSelector onSourceSelect={handleSourceSelect} />
      ) : (
        <>
          <button 
            className="back-btn" 
            onClick={handleBackToSelection}
          >
            ← Back to Database Selection
          </button>
          
          <ProblemView source={selectedSource} />
        </>
      )}
    </div>
  )
}
