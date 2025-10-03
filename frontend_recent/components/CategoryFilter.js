// components/CategoryFilter.js
const categories = [
  { value: 'all', label: '🌟 All Subjects', icon: '🌟' },
  { value: 'Geometry', label: '📐 Geometry', icon: '📐' },
  { value: 'Algebra', label: '🔢 Algebra', icon: '🔢' },
  { value: 'Number Theory', label: '🔢 Number Theory', icon: '🔢' },
  { value: 'Combinatorics', label: '🎲 Combinatorics', icon: '🎲' },
  { value: 'Mixed', label: '🌈 Mixed', icon: '🌈' },
];

export default function CategoryFilter({ selectedCategory, onCategoryChange }) {
  return (
    <div className="flex items-center gap-3">
      <label htmlFor="category-select" className="font-medium text-gray-700">
        🔬 Filter by Subject:
      </label>
      <select
        id="category-select"
        value={selectedCategory}
        onChange={(e) => onCategoryChange(e.target.value)}
        className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500 focus:border-green-500"
      >
        {categories.map((category) => (
          <option key={category.value} value={category.value}>
            {category.label}
          </option>
        ))}
      </select>
    </div>
  );
}
