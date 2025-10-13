import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { authAPI } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

export default function VerifyEmail() {
  const { token: routeToken } = useParams<{ token?: string }>()
  const [searchParams] = useSearchParams()
  const verificationToken = searchParams.get('token') ?? routeToken
  const navigate = useNavigate()
  const { setUser } = useAuth()
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying')
  const [error, setError] = useState('')

  useEffect(() => {
    const verify = async () => {
      if (!verificationToken) {
        setStatus('error')
        setError('Invalid verification link')
        return
      }

      try {
        const { data } = await authAPI.verifyEmail(verificationToken)
        setUser(data.user)
        setStatus('success')

        const timer = setTimeout(() => navigate('/dashboard'), 3000)
        return () => clearTimeout(timer)
      } catch (err: any) {
        console.error('Email verification error:', err)
        setStatus('error')
        setError(err?.response?.data?.error ?? 'Failed to verify email. The link may have expired.')
      }
    }

    verify()
  }, [verificationToken, navigate, setUser])

  const renderContent = () => {
    switch (status) {
      case 'verifying':
        return (
          <div className="flex flex-col items-center space-y-4 text-center">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
            <h2 className="text-2xl font-bold">Verifying your email...</h2>
            <p className="text-neutral-600">Please wait while we verify your email address.</p>
          </div>
        )
      case 'success':
        return (
          <div className="flex flex-col items-center space-y-4 text-center">
            <div className="rounded-full bg-green-100 p-3">
              <CheckCircle className="h-12 w-12 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold">Email Verified!</h2>
            <p className="text-neutral-600">
              Your email has been successfully verified. Redirecting to the dashboard...
            </p>
          </div>
        )
      default:
        return (
          <div className="flex flex-col items-center space-y-4 text-center">
            <div className="rounded-full bg-red-100 p-3">
              <AlertCircle className="h-12 w-12 text-red-600" />
            </div>
            <h2 className="text-2xl font-bold">Verification Failed</h2>
            <p className="text-neutral-600">{error}</p>
            <button
              className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-500"
              onClick={() => navigate('/login')}
            >
              Back to Login
            </button>
          </div>
        )
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-100 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow">
        <h1 className="mb-6 text-center text-2xl font-semibold">Email Verification</h1>
        {renderContent()}
      </div>
    </div>
  )
}