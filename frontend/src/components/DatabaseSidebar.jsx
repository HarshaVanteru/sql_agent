import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import AddDatabaseModal from './AddDatabaseModal'

export default function DatabaseSidebar({ selectedDb, onSelectDb, onRefresh }) {
  const { token } = useAuth()
  const [databases, setDatabases] = useState([])
  const [loading, setLoading] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState(null)

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

  const handleDelete = async (dbId, dbName) => {
    if (!token) return

    setDeleting(true)
    setError(null)
    try {
      const response = await fetch(`http://localhost:8000/api/databases/${dbId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        setDeleteConfirm(null)
        if (selectedDb?.id === dbId) {
          onSelectDb(null)
        }
        fetchDatabases()
      } else {
        const data = await response.json()
        setError(data.detail?.message || 'Failed to delete database')
      }
    } catch (error) {
      console.error('Failed to delete database:', error)
      setError('Failed to delete database')
    } finally {
      setDeleting(false)
    }
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
          {error && (
            <div className="p-3 m-2 bg-red-900 text-red-200 rounded-lg text-sm">
              {error}
            </div>
          )}
          {loading ? (
            <div className="p-4 text-gray-400">Loading...</div>
          ) : databases.length === 0 ? (
            <div className="p-4 text-gray-400 text-center text-sm">
              No databases yet. Add one to get started.
            </div>
          ) : (
            <div className="space-y-2 p-4">
              {databases.map(db => (
                <div key={db.id} className="group relative">
                  <button
                    onClick={() => onSelectDb(db)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedDb?.id === db.id
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="font-medium truncate">{db.name}</div>
                        <div className="text-xs opacity-75 mt-1">{db.db_type}</div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setDeleteConfirm(db)
                        }}
                        className={`ml-2 p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity ${
                          selectedDb?.id === db.id
                            ? 'text-red-200 hover:bg-red-600'
                            : 'text-red-400 hover:bg-red-900/30'
                        }`}
                        title="Delete database"
                      >
                        ✕
                      </button>
                    </div>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {showModal && (
        <AddDatabaseModal onClose={() => setShowModal(false)} onAdded={handleDbAdded} />
      )}

      {/* Delete Confirmation Dialog */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-bold text-white mb-2">Delete Database?</h3>
            <p className="text-gray-300 mb-4">
              Are you sure you want to delete <strong>{deleteConfirm.name}</strong>? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                disabled={deleting}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteConfirm.id, deleteConfirm.name)}
                disabled={deleting}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
