export default function Queries() {
  const queries = []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Queries</h1>
        <p className="text-gray-600 mt-1">View and manage your query history</p>
      </div>

      {queries.length === 0 ? (
        <div className="bg-white rounded-lg p-12 text-center shadow">
          <div className="text-6xl mb-4">💬</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No queries yet</h2>
          <p className="text-gray-600 mb-6">Run your first query from the Dashboard</p>
          <a
            href="/dashboard"
            className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
          >
            Go to Dashboard
          </a>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Query</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Database</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Date</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
              </tr>
            </thead>
            <tbody>
              {queries.map((query) => (
                <tr key={query.id} className="border-b hover:bg-gray-50">
                  <td className="px-6 py-3 text-sm text-gray-900">{query.text}</td>
                  <td className="px-6 py-3 text-sm text-gray-600">{query.database}</td>
                  <td className="px-6 py-3 text-sm text-gray-600">{query.date}</td>
                  <td className="px-6 py-3 text-sm">
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold">
                      {query.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
