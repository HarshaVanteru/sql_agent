import { Link, useLocation } from 'react-router-dom'

export default function DashboardSidebar({ onLogout }) {
  const location = useLocation()

  const links = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/dashboard/databases', label: 'Databases', icon: '🗄️' },
    { path: '/dashboard/queries', label: 'Queries', icon: '💬' },
    { path: '/dashboard/settings', label: 'Settings', icon: '⚙️' },
  ]

  return (
    <aside className="w-64 bg-gray-900 text-white p-6 flex flex-col">
      <div className="mb-8">
        <h2 className="text-2xl font-bold">QueryAI</h2>
      </div>

      <nav className="flex-1 space-y-2">
        {links.map((link) => (
          <Link
            key={link.path}
            to={link.path}
            className={`block px-4 py-3 rounded-lg transition-colors ${
              location.pathname === link.path
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-800'
            }`}
          >
            <span className="mr-2">{link.icon}</span>
            {link.label}
          </Link>
        ))}
      </nav>

      <button
        onClick={onLogout}
        className="w-full px-4 py-3 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition-colors"
      >
        Logout
      </button>
    </aside>
  )
}
