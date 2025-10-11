type DatabaseSource = 'imo' | 'putnam' | 'mit'

interface DatabaseInfo {
  id: DatabaseSource
  name: string
  description: string
  color: string
  icon: string
}

const databases: DatabaseInfo[] = [
  {
    id: 'imo',
    name: 'IMO (AoPS)',
    description: 'International Mathematical Olympiad problems from Art of Problem Solving',
    color: '#3b82f6',
    icon: '🏆'
  },
  {
    id: 'putnam',
    name: 'Putnam',
    description: 'William Lowell Putnam Mathematical Competition problems',
    color: '#10b981',
    icon: '📐'
  },
  {
    id: 'mit',
    name: 'MIT',
    description: 'MIT Integration Bee and contest problems',
    color: '#8b5cf6',
    icon: '∫'
  }
]

interface DatabaseSelectorProps {
  onSourceSelect: (source: DatabaseSource) => void
}

export default function DatabaseSelector({ onSourceSelect }: DatabaseSelectorProps) {
  return (
    <div className="source-grid">
      {databases.map((db) => (
        <div
          key={db.id}
          className="source-card"
          onClick={() => onSourceSelect(db.id)}
          style={{ '--accent-color': db.color } as React.CSSProperties}
        >
          <div className="source-icon">{db.icon}</div>
          <h3 className="source-title">{db.name}</h3>
          <p className="source-description">{db.description}</p>
          
          <div className="source-stats">
            {db.id === 'imo' && (
              <>
              </>
            )}
            {db.id === 'putnam' && (
              <>
              </>
            )}
            {db.id === 'mit' && (
              <>
              </>
            )}
          </div>
          
          <div className="source-arrow">→</div>
        </div>
      ))}
    </div>
  )
}