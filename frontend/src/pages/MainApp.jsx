import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import DatabaseSidebar from '../components/DatabaseSidebar'
import QueryInterface from '../components/QueryInterface'

export default function MainApp() {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const [selectedDb, setSelectedDb] = useState(null)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <DatabaseSidebar
        selectedDb={selectedDb}
        onSelectDb={setSelectedDb}
        onRefresh={refreshTrigger}
      />
      <QueryInterface selectedDb={selectedDb} onLogout={handleLogout} />
    </div>
  )
}
