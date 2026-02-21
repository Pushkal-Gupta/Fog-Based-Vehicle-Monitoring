"use client"


import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Link } from "@tanstack/react-router"

import { createUserWithEmailAndPassword } from "firebase/auth"
import { auth } from "@/lib/firebase"
import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"




export function SignupForm({
  className,
  ...props
}: React.ComponentProps<"form">) {

  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [email, setEmail] = useState<string>("")
  const [password, setPassword] = useState<string>("")
  const [confirmPassword, setConfirmPassword] = useState<string>("")
  const [fullName, setFullName] = useState<string>("")
  const handleSignup = async () => {
    try {
      setError(null)

      await createUserWithEmailAndPassword(auth, email, password)

      // After successful signup
      navigate({ to: "/" })
    } catch (err: any) {
      setError(err.message)
    }
  }

  const isFormValid =
    fullName.trim().length > 0 &&
    email.trim().length > 0 &&
    password.length >= 8 &&
    confirmPassword.length > 0 &&
    confirmPassword === password
  return (
    <form className={cn("flex flex-col gap-6", className)} {...props} onSubmit={(e) => {
      e.preventDefault()
      handleSignup().then(() => {
        console.log('Successfully created a new user');
      })
    }} >
      <FieldGroup>
        <div className="flex flex-col items-center gap-1 text-center">
          <h1 className="text-2xl font-bold">Create your account</h1>
          <p className="text-muted-foreground text-sm text-balance">
            Fill in the form below to create your account
          </p>
        </div>
        <Field>
          <FieldLabel htmlFor="name">Full Name</FieldLabel>
          <Input
            id="name"
            type="text"
            placeholder="John Doe"
            required
            value={fullName}
            className="bg-background"
            onChange={(e) => setFullName(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="email">Email</FieldLabel>
          <Input
            id="email"
            type="email"
            placeholder="m@example.com"
            required
            value={email}
            className="bg-background"
            onChange={(e) => setEmail(e.target.value)}

          />
          <FieldDescription>
            We&apos;ll use this to contact you. We will not share your email
            with anyone else.
          </FieldDescription>
        </Field>
        <Field>
          <FieldLabel htmlFor="password">Password</FieldLabel>
          <Input
            id="password"
            type="password"
            required
            value={password}
            className="bg-background"
            onChange={(e) => setPassword(e.target.value)}
          />
          <FieldDescription>
            Must be at least 8 characters long.
          </FieldDescription>
        </Field>
        <Field >
          <FieldLabel htmlFor="confirm-password">Confirm Password</FieldLabel>
          <Input
            aria-invalid={confirmPassword !== password && confirmPassword.length > 0}
            id="confirm-password"
            type="password"
            value={confirmPassword}
            required
            className="bg-background"
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
          <FieldDescription>{(confirmPassword !== password) ? "Passwords don't match." : "Please confirm your password."}</FieldDescription>
        </Field>
        <Field>
          <Button disabled={!isFormValid} type="submit">Create Account</Button>
        </Field>
        <Field>
          <FieldDescription className="px-6 text-center">
            Already have an account? <Link to="/login" >Login</Link>
          </FieldDescription>
        </Field>
      </FieldGroup>
    </form>
  )
}
