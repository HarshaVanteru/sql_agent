import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function NotFound() {
  const { isAuthenticated } = useAuth()

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-900 mb-4">404</h1>
        <p className="text-2xl text-gray-600 mb-8">Page not found</p>
        <p className="text-gray-500 mb-12 max-w-md">
          Sorry, the page you're looking for doesn't exist or has been moved.
        </p>
        <Link
          to={isAuthenticated ? '/dashboard' : '/'}
          className="inline-block px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
        >
          {isAuthenticated ? 'Back to Dashboard' : 'Back to Home'}
        </Link>
      </div>
    </div>
  )
}
