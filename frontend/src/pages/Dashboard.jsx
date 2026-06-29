import { useState } from 'react'
import DatabaseSidebar from '../components/DatabaseSidebar'
import QueryInterface from '../components/QueryInterface'

export default function Dashboard() {
  const [selectedDb, setSelectedDb] = useState(null)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  return (
    <div className="flex h-full gap-6">
      {/* Database Sidebar */}
      <div className="w-80 bg-white rounded-lg shadow p-4 overflow-y-auto">
        <DatabaseSidebar
          selectedDb={selectedDb}
          onSelectDb={setSelectedDb}
          onRefresh={refreshTrigger}
        />
      </div>

      {/* Query Interface */}
      <div className="flex-1 bg-white rounded-lg shadow overflow-hidden">
        <QueryInterface selectedDb={selectedDb} onLogout={() => {}} />
      </div>
    </div>
  )
}
