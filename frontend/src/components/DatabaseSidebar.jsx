import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import AddDatabaseModal from './AddDatabaseModal'

export default function DatabaseSidebar({ selectedDb, onSelectDb, onRefresh }) {
  const { token } = useAuth()
  const [databases, setDatabases] = useState([])
  const [loading, setLoading] = useState(false)
  const [showModal, setShowModal] = useState(false)

  const fetchDatabases = async () => {
    if (!token) return

    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/databases', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const data = await response.json()
        setDatabases(data.databases || [])
      }
    } catch (error) {
      console.error('Failed to fetch databases:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDatabases()
  }, [token, onRefresh])

  const handleDbAdded = () => {
    setShowModal(false)
    fetchDatabases()
  }

  return (
    <>
      <div className="w-64 bg-gray-900 text-white flex flex-col h-full">
        {/* Header */}
        <div className="p-4 border-b border-gray-700">
          <h1 className="text-xl font-bold mb-4">Databases</h1>
          <button
            onClick={() => setShowModal(true)}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            + Add Database
          </button>
        </div>

        {/* Database List */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-4 text-gray-400">Loading...</div>
          ) : databases.length === 0 ? (
            <div className="p-4 text-gray-400 text-center text-sm">
              No databases yet. Add one to get started.
            </div>
          ) : (
            <div className="space-y-2 p-4">
              {databases.map(db => (
                <button
                  key={db.id}
                  onClick={() => onSelectDb(db)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    selectedDb?.id === db.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  <div className="font-medium truncate">{db.name}</div>
                  <div className="text-xs opacity-75 mt-1">{db.db_type}</div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {showModal && (
        <AddDatabaseModal onClose={() => setShowModal(false)} onAdded={handleDbAdded} />
      )}
    </>
  )
}
