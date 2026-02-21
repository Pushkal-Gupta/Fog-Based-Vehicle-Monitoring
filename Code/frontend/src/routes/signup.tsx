import { SignupForm } from '@/components/signup-form'
import { createFileRoute } from '@tanstack/react-router'

import { Car } from 'lucide-react'

export const Route = createFileRoute('/signup')({
  component: SignUpPage,
})

function SignUpPage() {
  return (
    <div>
      <div className="grid min-h-svh lg:grid-cols-2">
        <div className="flex flex-col gap-4 p-6 md:p-10">
          <div className="flex justify-center gap-2 md:justify-start">
            <a href="#" className="flex items-center gap-2 font-medium">
              <div className="bg-primary text-primary-foreground flex p-3 items-center justify-center rounded-md">
                <Car className="size-5" />
              </div>
              Vehicle Monitoring Dashboard
            </a>
          </div>

          <div className="flex flex-1 items-center justify-center">
            <div className="w-full max-w-xs">
              <SignupForm />
            </div>
          </div>
        </div>
        <div className="bg-muted relative hidden lg:block">
          <img
            src="https://plus.unsplash.com/premium_photo-1693810032530-de2449b95389?q=80&w=687&auto=format&fit=crop&ixlib=rb-4.1.0"
            alt="Image"
            className="absolute inset-0 h-full w-full object-cover dark:brightness-[0.2] grayscale"
          />
        </div>
      </div>
    </div>
  )
}