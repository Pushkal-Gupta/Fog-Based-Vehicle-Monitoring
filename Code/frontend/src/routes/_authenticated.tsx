import { createFileRoute, Outlet } from '@tanstack/react-router'
import { useAuth } from '@/context/AuthContext'
import { useNavigate } from '@tanstack/react-router'
import { useEffect } from 'react'

export const Route = createFileRoute('/_authenticated')({
  component: AuthenticatedLayout,
})

function AuthenticatedLayout() {
  const { user, loading } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!loading && !user) {
      navigate({ to: '/login' })
    }
  }, [user, loading, navigate])

  if (loading) {
    return <div>Loading...</div>
  }

  if (!user) {
    return null
  }

  return <Outlet />
}