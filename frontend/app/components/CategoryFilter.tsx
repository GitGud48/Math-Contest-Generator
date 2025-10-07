type DatabaseSource = 'imo' | 'putnam' | 'mit'

interface CategoryFilterProps {
  source: DatabaseSource
  categories: string[]
  selectedCategory: string
  onCategoryChange: (category: string) => void
  totalProblems: number
}

export default function CategoryFilter({ 
  source, 
  categories,
  selectedCategory, 
  onCategoryChange,
  totalProblems
}: CategoryFilterProps) {

  const getCategoryLabel = () => {
    switch (source) {
      case 'imo':
        return 'Subject Area'
      case 'putnam':
        return 'Part'
      case 'mit':
        return 'Category'
      default:
        return 'Category'
    }
  }

  if (categories.length === 0) {
    return null
  }

  return (
    <div className="category-filter">
      <h3 className="filter-title">Filter by {getCategoryLabel()}</h3>
      
      <div className="category-buttons">
        <button
          className={`category-btn ${selectedCategory === 'all' ? 'active' : ''}`}
          onClick={() => onCategoryChange('all')}
        >
          All
          <span className="count">({totalProblems})</span>
        </button>
        
        {categories.map(category => (
          <button
            key={category}
            className={`category-btn ${selectedCategory === category ? 'active' : ''}`}
            onClick={() => onCategoryChange(category)}
          >
            {category}
          </button>
        ))}
      </div>
      
      {/* Additional filters for different sources */}
      {source === 'imo' && categories.length > 3 && (
        <div className="filter-hint">
          <p>💡 IMO problems are categorized by mathematical subject areas</p>
        </div>
      )}
      
      {source === 'putnam' && (
        <div className="filter-hint">
          <p>💡 Putnam problems are divided into Part A and Part B, with increasing difficulty</p>
        </div>
      )}
      
      {source === 'mit' && (
        <div className="filter-hint">
          <p>💡 MIT problems focus on integration techniques and calculus applications</p>
        </div>
      )}
    </div>
  )
}