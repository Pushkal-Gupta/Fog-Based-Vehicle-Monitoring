import { createFileRoute, Outlet, redirect } from '@tanstack/react-router'
import { auth } from '@/lib/firebase'

export const Route = createFileRoute('/_authenticated')({
  beforeLoad: ({ location }) => {
    if (!auth.currentUser) {
      throw redirect({
        to: '/login',
        search: {
          redirect: location.href,
        },
      })
    }
  },
  component: AuthenticatedLayout,
})


function AuthenticatedLayout() {
  return <Outlet />
}