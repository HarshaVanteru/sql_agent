import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import DatabaseSidebar from '../components/DatabaseSidebar'
import ConversationSidebar from '../components/ConversationSidebar'
import QueryInterface from '../components/QueryInterface'

export default function MainApp() {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const [selectedDb, setSelectedDb] = useState(null)
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [activeConversationId, setActiveConversationId] = useState(null)
  // Bumped after each turn so the conversation list re-fetches its titles,
  // ordering, and message counts.
  const [convRefreshKey, setConvRefreshKey] = useState(0)

  const handleLogout = () => {
    logout()
    navigate('/auth/login')
  }

  const handleSelectDb = (db) => {
    setSelectedDb(db)
    // A conversation belongs to one database; switching starts fresh.
    setActiveConversationId(null)
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <DatabaseSidebar
        selectedDb={selectedDb}
        onSelectDb={handleSelectDb}
        onRefresh={refreshTrigger}
      />
      <ConversationSidebar
        selectedDb={selectedDb}
        activeConversationId={activeConversationId}
        refreshKey={convRefreshKey}
        onSelectConversation={setActiveConversationId}
        onNewConversation={() => setActiveConversationId(null)}
      />
      <QueryInterface
        selectedDb={selectedDb}
        activeConversationId={activeConversationId}
        onConversationChange={setActiveConversationId}
        onTurnComplete={() => setConvRefreshKey(k => k + 1)}
        onLogout={handleLogout}
      />
    </div>
  )
}
