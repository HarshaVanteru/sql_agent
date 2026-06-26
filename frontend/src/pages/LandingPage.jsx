import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useEffect } from 'react'

export default function LandingPage() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/app')
    }
  }, [isAuthenticated, navigate])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4 sm:px-6 lg:px-8">
      <div className="text-center">
        <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
          Database Query Assistant
        </h1>
        <p className="text-xl md:text-2xl text-gray-600 mb-12 max-w-2xl">
          Connect your databases and ask natural language queries. Get insights instantly.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/signup"
            className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors text-lg"
          >
            Sign Up
          </Link>
          <Link
            to="/login"
            className="px-8 py-4 bg-white hover:bg-gray-50 text-blue-600 font-semibold border-2 border-blue-600 rounded-lg transition-colors text-lg"
          >
            Sign In
          </Link>
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl">
          <div className="bg-white rounded-lg p-6 shadow-md">
            <div className="text-4xl mb-4">🗄️</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Connect Databases</h3>
            <p className="text-gray-600">Add your database credentials securely</p>
          </div>
          <div className="bg-white rounded-lg p-6 shadow-md">
            <div className="text-4xl mb-4">💬</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Natural Language</h3>
            <p className="text-gray-600">Ask questions in plain English</p>
          </div>
          <div className="bg-white rounded-lg p-6 shadow-md">
            <div className="text-4xl mb-4">⚡</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Instant Results</h3>
            <p className="text-gray-600">Get answers immediately</p>
          </div>
        </div>
      </div>
    </div>
  )
}
