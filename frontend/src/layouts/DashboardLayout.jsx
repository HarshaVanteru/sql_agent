import { useNavigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import DashboardSidebar from '../components/DashboardSidebar'

export default function DashboardLayout() {
  const navigate = useNavigate()
  const { logout } = useAuth()

  const handleLogout = () => {
    logout()
    navigate('/auth/login')
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <DashboardSidebar onLogout={handleLogout} />
      <div className="flex-1 flex flex-col">
        <div className="flex items-center justify-between px-8 py-4 bg-white border-b">
          <h1 className="text-2xl font-bold text-gray-900">Database Query Assistant</h1>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition-colors"
          >
            Logout
          </button>
        </div>
        <div className="flex-1 overflow-auto p-8">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
