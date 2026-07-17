import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useApi } from '../api/useApi'

function timeAgo(iso) {
  if (!iso) return ''
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return new Date(iso).toLocaleDateString()
}

export default function ConversationSidebar({
  selectedDb,
  activeConversationId,
  refreshKey,
  onSelectConversation,
  onNewConversation,
}) {
  const { token } = useAuth()
  const api = useApi()
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(false)

  const fetchConversations = async () => {
    if (!selectedDb || !token) return

    setLoading(true)
    try {
      const data = await api.get(`/api/databases/${selectedDb.id}/conversations`)
      setConversations(data.conversations || [])
    } catch (error) {
      console.error('Failed to fetch conversations:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (selectedDb) {
      fetchConversations()
    } else {
      setConversations([])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDb, token, refreshKey])

  if (!selectedDb) {
    return (
      <div className="w-72 bg-white border-r border-gray-200 flex items-center justify-center">
        <p className="text-sm text-gray-400 text-center px-4">
          Select a database to see its conversations
        </p>
      </div>
    )
  }

  return (
    <div className="w-72 bg-white border-r border-gray-200 flex flex-col h-full">
      <div className="p-4 border-b border-gray-200">
        <button
          onClick={onNewConversation}
          className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
        >
          + New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading && conversations.length === 0 ? (
          <div className="p-4 text-gray-400 text-sm">Loading...</div>
        ) : conversations.length === 0 ? (
          <div className="p-4 text-gray-400 text-center text-sm">
            No conversations yet. Ask a question to start one.
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {conversations.map(conv => (
              <button
                key={conv.id}
                onClick={() => onSelectConversation(conv.id)}
                className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                  activeConversationId === conv.id
                    ? 'bg-blue-100 text-blue-900'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <div className="font-medium text-sm truncate">
                  {conv.title || 'Untitled conversation'}
                </div>
                <div className="text-xs text-gray-500 mt-0.5 flex justify-between">
                  <span>{timeAgo(conv.updated_at)}</span>
                  <span>{conv.message_count} msg</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
