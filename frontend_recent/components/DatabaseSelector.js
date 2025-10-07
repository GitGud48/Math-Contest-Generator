// components/DatabaseSelector.js
const expectedDatabases = {
  'mit': { name: '🏛️ MIT Problems', icon: '🏛️' },
  'putnam': { name: '🏆 Putnam Competition', icon: '🏆' },
  'imo': { name: '🌍 International Mathematical Olympiad', icon: '🌍' }
};

export default function DatabaseSelector({ databases, selectedDatabase, onDatabaseChange }) {
  const handleChange = (e) => {
    console.log('Database selected:', e.target.value); // Debug log
    onDatabaseChange(e.target.value);
  };

  return (
    <div className="flex items-center gap-3">
      <label htmlFor="database-select" className="font-medium text-gray-700">
        📚 Choose Database:
      </label>
      <select
        id="database-select"
        value={selectedDatabase}
        onChange={handleChange}
        className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-w-64"
      >
        <option value="">Select a database...</option>
        {databases.map((db) => (
          <option key={db.id} value={db.id}>
            {expectedDatabases[db.id]?.name || db.name} ({db.problem_count} problems)
          </option>
        ))}
      </select>
    </div>
  );
}
