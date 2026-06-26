import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

export default function QueryInterface({ selectedDb, onLogout }) {
  const { token, user, refreshAccessToken } = useAuth()
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
  const [queryMode, setQueryMode] = useState('natural') // 'natural' or 'sql'
  const messagesEndRef = useRef(null)

  const executeQuery = async (query, currentToken, mode = 'natural') => {
    const endpoint = mode === 'sql' ? 'query' : 'natural-query'
    const bodyKey = mode === 'sql' ? 'query' : 'question'

    const response = await fetch(`http://localhost:8000/api/databases/${selectedDb.id}/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${currentToken}`,
      },
      body: JSON.stringify({ [bodyKey]: query }),
    })

    if (response.status === 401) {
      // Token expired, try to refresh
      const refreshResult = await refreshAccessToken()
      if (refreshResult.success) {
        // Retry with new token
        return executeQuery(query, localStorage.getItem('auth_token'), mode)
      } else {
        throw new Error('Session expired. Please log in again.')
      }
    }

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail?.message || 'Query execution failed')
    }

    return response.json()
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (selectedDb) {
      const isMongoDb = selectedDb.db_type?.toLowerCase() === 'mongodb'
      const connectionInfo = isMongoDb
        ? `Connected to MongoDB: ${selectedDb.name}\n\nQuery Format: collection_name\n{filter_json_optional}`
        : `Connected to database: ${selectedDb.name}\n\nYou can use natural language or SQL queries.`

      setMessages([
        {
          id: 1,
          type: 'system',
          content: connectionInfo,
        },
      ])

      // Auto-switch to SQL mode for MongoDB
      if (isMongoDb && queryMode === 'natural') {
        setQueryMode('sql')
      }
    }
  }, [selectedDb])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || !selectedDb) return

    const userMessage = {
      id: messages.length + 1,
      type: 'user',
      content: input,
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const data = await executeQuery(input, token, queryMode)

      const assistantMessage = {
        id: messages.length + 2,
        type: 'query_result',
        sql: data.sql || null,
        columns: data.columns || [],
        rows: data.rows || [],
        row_count: data.row_count || 0,
      }
      setMessages(prev => [...prev, assistantMessage])
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

  return (
    <div className="flex-1 bg-white flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {selectedDb ? selectedDb.name : 'Database Query Assistant'}
          </h1>
          {selectedDb && (
            <p className="text-sm text-gray-600 mt-1">Type a query to get started</p>
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
              <div className="max-w-2xl px-4 py-3 rounded-lg bg-blue-600 text-white">
                <p className="text-sm">{msg.content}</p>
              </div>
            ) : msg.type === 'error' ? (
              <div className="max-w-2xl w-full px-4 py-3 rounded-lg bg-red-100 text-red-700 border border-red-300">
                <p className="text-sm font-semibold">Error</p>
                <p className="text-sm mt-1">{msg.content}</p>
              </div>
            ) : msg.type === 'system' ? (
              <div className="max-w-2xl w-full px-4 py-3 rounded-lg bg-gray-200 text-gray-900">
                <p className="text-sm">{msg.content}</p>
              </div>
            ) : msg.type === 'query_result' ? (
              <div className="max-w-5xl w-full space-y-3">
                {msg.sql && (
                  <div className="bg-white rounded-lg border border-gray-200 p-4">
                    <p className="text-xs font-semibold text-gray-600 mb-2">Generated SQL:</p>
                    <pre className="bg-gray-900 text-gray-100 p-3 rounded text-xs overflow-x-auto">
                      <code>{msg.sql}</code>
                    </pre>
                  </div>
                )}

                {msg.row_count === 0 ? (
                  <div className="bg-white rounded-lg border border-gray-200 p-4">
                    <p className="text-sm text-gray-700">Query executed successfully. No results returned.</p>
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
              {selectedDb?.db_type?.toLowerCase() !== 'mongodb' && (
                <button
                  onClick={() => setQueryMode('natural')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    queryMode === 'natural'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Natural Language
                </button>
              )}
              <button
                onClick={() => setQueryMode('sql')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  queryMode === 'sql'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {selectedDb?.db_type?.toLowerCase() === 'mongodb' ? 'Query' : 'SQL'}
              </button>
            </div>
            {selectedDb?.db_type?.toLowerCase() === 'mongodb' && (
              <div className="text-xs text-gray-600 bg-gray-100 p-2 rounded">
                <p className="font-semibold mb-1">MongoDB Query Format:</p>
                <p>Line 1: collection_name</p>
                <p>Line 2 (optional): JSON filter object</p>
                <p className="mt-1 text-gray-500">Example: users</p>
                <p className="text-gray-500">{'{\"age\": {\"$gte\": 18}}'}</p>
              </div>
            )}
            <form onSubmit={handleSubmit} className="flex gap-3">
              <textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder={
                  selectedDb?.db_type?.toLowerCase() === 'mongodb'
                    ? 'collection_name\n{"filter": "value"}'
                    : queryMode === 'sql'
                    ? 'Enter SQL query...'
                    : 'Ask a question about your data...'
                }
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                disabled={loading}
                rows={selectedDb?.db_type?.toLowerCase() === 'mongodb' ? 3 : 1}
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
