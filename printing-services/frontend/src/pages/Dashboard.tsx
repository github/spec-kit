import { useAuth } from '../contexts/AuthContext'

export default function Dashboard() {
  const { user } = useAuth()

  return (
    <div className="animate-fade-in">
      <h1 className="text-3xl font-bold text-gradient mb-6">
        Welcome back, {user?.firstName || user?.email}!
      </h1>
      <div className="grid md:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="font-semibold text-lg mb-2">Active Requests</h3>
          <p className="text-3xl font-bold text-primary-600">0</p>
        </div>
        <div className="card">
          <h3 className="font-semibold text-lg mb-2">Pending Proposals</h3>
          <p className="text-3xl font-bold text-secondary-600">0</p>
        </div>
        <div className="card">
          <h3 className="font-semibold text-lg mb-2">Messages</h3>
          <p className="text-3xl font-bold text-green-600">0</p>
        </div>
      </div>
    </div>
  )
}
