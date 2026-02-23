"use client"

import { useState } from "react"
import { useNavigate } from "@tanstack/react-router"
import { signInWithEmailAndPassword } from "firebase/auth"
import { auth } from "@/lib/firebase"
import { toast } from "sonner"

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

export function LoginForm({
  className,
  ...props
}: React.ComponentProps<"form">) {
  const navigate = useNavigate()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      await signInWithEmailAndPassword(auth, email, password)

      toast.success("Login successful 🎉")

      navigate({ to: "/" })
    } catch (err: any) {
      if (
        err.code === "auth/user-not-found" ||
        err.code === "auth/wrong-password" ||
        err.code === "auth/invalid-credential"
      ) {
        toast.error("Account does not exist or wrong email and password.")
      } else {
        toast.error("Something went wrong. Please try again.")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <form
      onSubmit={handleLogin}
      className={cn("flex flex-col gap-6", className)}
      {...props}
    >
      <FieldGroup>
        <div className="flex flex-col items-center gap-1 text-center">
          <h1 className="text-2xl font-bold">Login to your account</h1>
          <p className="text-muted-foreground text-sm text-balance">
            Enter your email below to login to your account
          </p>
        </div>

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
        </Field>

        <Field>
          <Button type="submit" disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </Button>
        </Field>

        <Field>
          <FieldDescription className="text-center">
            Don&apos;t have an account?{" "}
            <Link to="/signup">Sign up</Link>
          </FieldDescription>
        </Field>
      </FieldGroup>
    </form>
  )
}