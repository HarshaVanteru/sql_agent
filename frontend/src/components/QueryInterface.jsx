import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useApi } from '../api/useApi'

export default function QueryInterface({
  selectedDb,
  activeConversationId,
  onConversationChange,
  onTurnComplete,
  onLogout,
}) {
  const { user } = useAuth()
  const api = useApi()
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'system',
      content: selectedDb
        ? `Connected to database: ${selectedDb.name}`
        : 'Select a database from the sidebar to start querying',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [queryMode, setQueryMode] = useState('natural') // 'natural' or 'direct'
  const [conversationId, setConversationId] = useState(null)
  const messagesEndRef = useRef(null)
  // The conversation currently rendered. Lets us ignore the parent echoing back
  // an id this view already shows (e.g. one it just created) versus a genuine
  // request to load a different, past conversation.
  const syncedConvRef = useRef(null)

  const executeQuery = async (query, mode = 'natural') => {
    const endpoint = mode === 'direct' ? 'query' : 'natural-query'

    // Natural language turns carry the conversation so follow-ups like
    // "now only last month" resolve against the previous question.
    const body =
      mode === 'direct'
        ? { query }
        : { question: query, conversation_id: conversationId }

    return api.post(`/api/databases/${selectedDb.id}/${endpoint}`, body)
  }

  const greetingMessage = (db) => ({
    id: 1,
    type: 'system',
    content: `Connected to ${db.db_type}: ${db.name}\n\nAsk a question in plain English, or write a query yourself. Follow-ups keep the context of the previous question.`,
  })

  // Turn a stored message (GET .../conversations/{id}) into the shape this view
  // renders, mirroring what handleSubmit builds for a live turn.
  const storedToDisplay = (m) =>
    m.role === 'user'
      ? { id: m.id, type: 'user', content: m.content, mode: 'natural' }
      : {
          id: m.id,
          type: 'query_result',
          generatedQuery: m.sql_query || null,
          message: m.content || null,
          columns: m.result?.columns || [],
          rows: m.result?.rows || [],
          row_count: m.result?.row_count || 0,
        }

  const loadConversation = async (convId) => {
    setLoading(true)
    try {
      const data = await api.get(
        `/api/databases/${selectedDb.id}/conversations/${convId}`,
      )
      setMessages([greetingMessage(selectedDb), ...data.messages.map(storedToDisplay)])
      setConversationId(convId)
      syncedConvRef.current = convId
    } catch (error) {
      setMessages([
        { id: 1, type: 'system', content: greetingMessage(selectedDb).content },
        { id: 2, type: 'error', content: 'Failed to load conversation: ' + error.message },
      ])
    } finally {
      setLoading(false)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (!selectedDb) {
      setMessages([
        {
          id: 1,
          type: 'system',
          content: 'Select a database from the sidebar to start querying',
        },
      ])
      setConversationId(null)
      syncedConvRef.current = null
      return
    }

    // Default to natural language for all databases.
    setQueryMode('natural')

    // The parent is echoing back a conversation this view already shows (the one
    // it just created or loaded) — nothing to reload.
    if (activeConversationId && activeConversationId === syncedConvRef.current) return

    if (activeConversationId) {
      loadConversation(activeConversationId)
    } else {
      // New chat, or a database switch: start from a clean greeting.
      setMessages([greetingMessage(selectedDb)])
      setConversationId(null)
      syncedConvRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDb, activeConversationId])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || !selectedDb) return

    const userMessage = {
      id: messages.length + 1,
      type: 'user',
      content: input,
      mode: queryMode,
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const data = await executeQuery(input, queryMode)

      if (data.conversation_id) {
        setConversationId(data.conversation_id)
        // Mark as already displayed so the parent setting this id below does not
        // trigger a reload of the very turn we are about to render.
        syncedConvRef.current = data.conversation_id
        if (data.conversation_id !== activeConversationId) {
          onConversationChange?.(data.conversation_id)
        }
      }

      const assistantMessage = {
        id: messages.length + 2,
        type: 'query_result',
        generatedQuery: data.query || null,
        message: data.message || null,
        columns: data.columns || [],
        rows: data.rows || [],
        row_count: data.row_count || 0,
      }
      setMessages(prev => [...prev, assistantMessage])

      // Refresh the conversation list: a new turn changes titles, ordering
      // (most-recently-active first), and message counts.
      onTurnComplete?.()
    } catch (error) {
      const errorMessage = {
        id: messages.length + 2,
        type: 'error',
        content: 'Failed to execute query: ' + error.message,
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const getQueryTypeLabel = () => {
    if (queryMode === 'natural') {
      return 'Natural Language'
    }
    return 'SQL Query'
  }

  return (
    <div className="flex-1 bg-white flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {selectedDb ? selectedDb.name : 'Database Query Assistant'}
          </h1>
          {selectedDb && (
            <p className="text-sm text-gray-600 mt-1">
              {selectedDb.db_type} • {getQueryTypeLabel() === 'Natural Language' ? 'Ask questions' : 'Write queries'}
            </p>
          )}
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-gray-600">
            {user?.email}
          </div>
          <button
            onClick={onLogout}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex ${
              msg.type === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {msg.type === 'user' ? (
              <div className="max-w-2xl">
                <div className="px-4 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold mb-1">
                  {msg.mode === 'natural' ? '🤖 Natural Language' : '📝 Direct Query'}
                </div>
                <div className="px-4 py-3 rounded-lg bg-blue-600 text-white">
                  <p className="text-sm">{msg.content}</p>
                </div>
              </div>
            ) : msg.type === 'error' ? (
              <div className="max-w-2xl w-full px-4 py-3 rounded-lg bg-red-100 text-red-700 border border-red-300">
                <p className="text-sm font-semibold">Error</p>
                <p className="text-sm mt-1">{msg.content}</p>
              </div>
            ) : msg.type === 'system' ? (
              <div className="max-w-2xl w-full px-4 py-3 rounded-lg bg-gray-200 text-gray-900">
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            ) : msg.type === 'query_result' ? (
              <div className="max-w-5xl w-full space-y-3">
                {msg.generatedQuery && (
                  <div className="bg-white rounded-lg border border-gray-200 p-4">
                    <p className="text-xs font-semibold text-gray-600 mb-2">
                      Generated SQL:
                    </p>
                    <pre className="bg-gray-900 text-gray-100 p-3 rounded text-xs overflow-x-auto">
                      <code>{msg.generatedQuery}</code>
                    </pre>
                  </div>
                )}

                {msg.row_count === 0 ? (
                  <div className="bg-white rounded-lg border border-gray-200 p-4">
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {msg.message || 'Query executed successfully. No results returned.'}
                    </p>
                  </div>
                ) : (
                  <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                    <div className="p-4 border-b border-gray-200 bg-gray-50">
                      <p className="text-sm font-semibold text-gray-700">
                        Results: {msg.row_count} row(s)
                      </p>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="bg-gray-50 border-b border-gray-200">
                            {msg.columns.map((col, idx) => (
                              <th
                                key={idx}
                                className="px-4 py-3 text-left text-xs font-semibold text-gray-700"
                              >
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {msg.rows.map((row, rowIdx) => (
                            <tr
                              key={rowIdx}
                              className={`border-b border-gray-200 hover:bg-gray-50 transition-colors ${
                                rowIdx % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                              }`}
                            >
                              {msg.columns.map((col, colIdx) => (
                                <td
                                  key={colIdx}
                                  className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate"
                                  title={String(row[col])}
                                >
                                  {row[col] !== null && row[col] !== undefined
                                    ? String(row[col])
                                    : <span className="text-gray-400 italic">NULL</span>}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="max-w-2xl px-4 py-3 rounded-lg bg-gray-200 text-gray-900">
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 text-gray-900 px-4 py-3 rounded-lg">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce"></div>
                <p className="text-sm">Processing your query...</p>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white p-6">
        {!selectedDb ? (
          <div className="text-center text-gray-500 py-4">
            Select a database from the sidebar to start querying
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex gap-2">
              <button
                onClick={() => setQueryMode('natural')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  queryMode === 'natural'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                🤖 Natural Language
              </button>
              <button
                onClick={() => setQueryMode('direct')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  queryMode === 'direct'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                📝 SQL Query
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex gap-3">
              <textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder={
                  queryMode === 'natural'
                    ? 'Ask a question about your data...'
                    : 'Enter SQL query...'
                }
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                disabled={loading}
                rows={1}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors self-end"
              >
                Send
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  )
}
