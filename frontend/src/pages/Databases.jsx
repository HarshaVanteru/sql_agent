import { useState } from 'react'
import AddDatabaseModal from '../components/AddDatabaseModal'

export default function Databases() {
  const [showModal, setShowModal] = useState(false)
  const [databases, setDatabases] = useState([])

  const handleAddDatabase = (dbData) => {
    setDatabases([...databases, { id: Date.now(), ...dbData }])
    setShowModal(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Databases</h1>
          <p className="text-gray-600 mt-1">Manage your database connections</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
        >
          + Add Database
        </button>
      </div>

      {databases.length === 0 ? (
        <div className="bg-white rounded-lg p-12 text-center shadow">
          <div className="text-6xl mb-4">🗄️</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No databases yet</h2>
          <p className="text-gray-600 mb-6">Add your first database to get started</p>
          <button
            onClick={() => setShowModal(true)}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
          >
            Add Database
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {databases.map((db) => (
            <div key={db.id} className="bg-white rounded-lg p-6 shadow">
              <h3 className="text-lg font-semibold text-gray-900">{db.name}</h3>
              <p className="text-gray-600 text-sm mt-1">Type: {db.type}</p>
              <div className="mt-4 flex gap-2">
                <button className="flex-1 px-3 py-2 text-sm bg-gray-200 hover:bg-gray-300 rounded transition-colors">
                  Edit
                </button>
                <button className="flex-1 px-3 py-2 text-sm bg-red-200 hover:bg-red-300 text-red-700 rounded transition-colors">
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <AddDatabaseModal
          onClose={() => setShowModal(false)}
          onSubmit={handleAddDatabase}
        />
      )}
    </div>
  )
}
