import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { verifyEmail } from '@/services/api/auth'
import { useAuth } from '@/contexts/AuthContext'

export default function VerifyEmail() {
  const { token: routeToken } = useParams<{ token?: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const verificationToken = searchParams.get('token') ?? routeToken
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying')
  const [error, setError] = useState('')
  const { setUser } = useAuth()

  useEffect(() => {
    const verifyToken = async () => {
      if (!verificationToken) {
        setStatus('error')
        setError('Invalid verification link')
        return
      }

      try {
        const user = await verifyEmail(verificationToken)
        setUser(user)
        setStatus('success')
        
        // Redirect to dashboard after 3 seconds
        const timer = setTimeout(() => {
          navigate('/dashboard')
        }, 3000)
        
        return () => clearTimeout(timer)
      } catch (err) {
        console.error('Email verification error:', err)
        setStatus('error')
        setError(err.response?.data?.error || 'Failed to verify email. The link may have expired.')
      }
    }

    verifyToken()
  }, [verificationToken, navigate, setUser])

  const getStatusContent = () => {
    switch (status) {
      case 'verifying':
        return (
          <div className="flex flex-col items-center justify-center space-y-4 text-center">
            <Loader2 className="h-12 w-12 animate-spin text-primary-600" />
            <h2 className="text-2xl font-bold">Verifying your email...</h2>
            <p className="text-secondary-600">Please wait while we verify your email address.</p>
          </div>
        )
      case 'success':
        return (
          <div className="flex flex-col items-center justify-center space-y-4 text-center">
            <div className="rounded-full bg-green-100 p-3">
              <CheckCircle className="h-12 w-12 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold">Email Verified!</h2>
            <p className="text-secondary-600">Your email has been successfully verified. Redirecting to dashboard...</p>
          </div>
        )
      case 'error':
        return (
          <div className="flex flex-col items-center justify-center space-y-4 text-center">
            <div className="rounded-full bg-red-100 p-3">
              <AlertCircle className="h-12 w-12 text-red-600" />
            </div>
            <h2 className="text-2xl font-bold">Verification Failed</h2>
            <p className="text-secondary-600">{error}</p>
            <Button onClick={() => navigate('/login')}>
              Back to Login
            </Button>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-secondary-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center">Email Verification</CardTitle>
        </CardHeader>
        <CardContent>
          {getStatusContent()}
        </CardContent>
      </Card>
    </div>
  )
}
