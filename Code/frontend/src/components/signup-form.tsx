"use client"

import { useState } from "react"
import { useNavigate } from "@tanstack/react-router"
import { createUserWithEmailAndPassword, updateProfile } from "firebase/auth"
import { toast } from "sonner"

import { auth } from "@/lib/firebase"
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

export function SignupForm({
  className,
  ...props
}: React.ComponentProps<"form">) {

  const navigate = useNavigate()

  const [loading, setLoading] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [fullName, setFullName] = useState("")

  const isFormValid =
    fullName.trim().length > 0 &&
    email.trim().length > 0 &&
    password.length >= 8 &&
    confirmPassword === password

  const handleSignup = async () => {
    if (password !== confirmPassword) {
      toast.error("Passwords do not match.")
      return
    }

    try {
      setLoading(true)

      const userCredential = await createUserWithEmailAndPassword(
        auth,
        email,
        password
      )

      // Optional: store full name in Firebase user profile
      await updateProfile(userCredential.user, {
        displayName: fullName,
      })

      toast.success("Account created successfully 🎉")

      navigate({ to: "/" })

    } catch (err: any) {

      if (err.code === "auth/email-already-in-use") {
        toast.error("Account already exists with this email.")
      } else if (err.code === "auth/invalid-email") {
        toast.error("Invalid email format.")
      } else if (err.code === "auth/weak-password") {
        toast.error("Password must be at least 6 characters.")
      } else {
        toast.error("Something went wrong. Please try again.")
      }

    } finally {
      setLoading(false)
    }
  }

  return (
    <form
      className={cn("flex flex-col gap-6", className)}
      {...props}
      onSubmit={(e) => {
        e.preventDefault()
        handleSignup()
      }}
    >
      <FieldGroup>
        <div className="flex flex-col items-center gap-1 text-center">
          <h1 className="text-2xl font-bold">Create your account</h1>
          <p className="text-muted-foreground text-sm">
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
            We will not share your email with anyone.
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

        <Field>
          <FieldLabel htmlFor="confirm-password">
            Confirm Password
          </FieldLabel>
          <Input
            id="confirm-password"
            type="password"
            required
            value={confirmPassword}
            className="bg-background"
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
        </Field>

        <Field>
          <Button disabled={!isFormValid || loading} type="submit">
            {loading ? "Creating..." : "Create Account"}
          </Button>
        </Field>

        <Field>
          <FieldDescription className="px-6 text-center">
            Already have an account? <Link to="/login">Login</Link>
          </FieldDescription>
        </Field>
      </FieldGroup>
    </form>
  )
}