import * as React from "react"
import { Link, createFileRoute } from "@tanstack/react-router"
import { ArrowLeftIcon } from "lucide-react"
import { toast } from "sonner"
import { getAuth } from "firebase/auth"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
} from "@/components/ui/input-otp"
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"

export const Route = createFileRoute("/_authenticated/claim-vehicle")({
  component: ClaimVehiclePage,
})

function ClaimVehiclePage() {
  const [vehicleId, setVehicleId] = React.useState("")
  const [code, setCode] = React.useState("")

  const [loading, setLoading] = React.useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!vehicleId || code.length !== 6) {
      toast.error("Please enter a valid vehicle ID and 6-digit code.")
      return
    }

    try {
      setLoading(true)

      const auth = getAuth()
      const user = auth.currentUser

      if (!user) {
        toast.error("You must be logged in.")
        return
      }

      const token = await user.getIdToken()

      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/vehicle/claim`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            vehicle_id: vehicleId,
            activation_code: code,
          }),
        }
      )

      const data = await res.json()

      if (!res.ok) {
        // 400 → invalid vehicle ID or activation code
        if (res.status === 400 && data?.detail) {
          toast.error(data.detail)
          return
        }

        // 422 → validation errors (FastAPI schema)
        if (res.status === 422 && data?.detail?.length) {
          toast.error(data.detail[0].msg)
          return
        }

        // fallback
        toast.error("Failed to claim vehicle. Please try again.")
        return
      }

      toast.success(`Vehicle ${data.vehicle_id} claimed successfully!`)
      setVehicleId("")
      setCode("")
    } catch (error) {
      console.error(error)
      toast.error("Something went wrong.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full flex justify-center px-4 py-8">
      <div className="w-full max-w-2xl">
        <Card className="p-0">
          <CardHeader className="p-0 m-0 rounded-bl-none rounded-br-none rounded-xl ">
            <div
              
              style={{
                backgroundColor: "#3261de",
                opacity: 0.95,
                backgroundImage: `
                  repeating-radial-gradient(circle at 0 0, transparent 0, #3261de 10px),
                  repeating-linear-gradient(#4798fe55, #4798fe)
                `,
              }}
            >
              <div className="p-6 md:p-8 text-white">
                <h1 className="text-2xl md:text-3xl font-semibold">
                  Claim a vehicle
                </h1>
                <p className="text-sm md:text-base text-[#dbe7ff] mt-2">
                  Enter the vehicle ID and the 6-digit activation code.
                </p>
              </div>
            </div>
          </CardHeader>

          <CardContent className="p-6 md:p-8 space-y-8">
            <form
              onSubmit={handleSubmit}
              className="flex flex-col gap-8"
            >
              {/* Vehicle ID */}
              <div className="space-y-2">

                <Field>
                  <FieldLabel>Vehicle ID</FieldLabel>
                  <Input
                    placeholder="Enter vehicle ID"
                    value={vehicleId}
                    onChange={(e) => setVehicleId(e.target.value)}
                    className="h-12 text-base"
                  />
                </Field>

              </div>

              {/* Activation Code */}
              <div className="space-y-4">
                <Field>
                  <FieldLabel>
                    Verfication Code
                  </FieldLabel>
                  <InputOTP
                    maxLength={6}
                    value={code}
                    onChange={setCode}
                    className="w-full"
                  >
                    <InputOTPGroup className="flex w-full">
                      {[...Array(6)].map((_, i) => (
                        <InputOTPSlot
                          key={i}
                          index={i}
                          className="
          flex-1
          h-14 md:h-16
          text-xl md:text-2xl
        "
                        />
                      ))}
                    </InputOTPGroup>
                  </InputOTP>
                </Field>

              </div>

              {/* Submit */}
              <Button
                type="submit"
                className="h-12 text-base font-medium"
                disabled={loading}
              >
                {loading ? "Claiming..." : "Claim Vehicle"}
              </Button>
            </form>

            {/* Go Back Home */}
            <div className="flex justify-center pt-4">
              <Link to="/">
                <Button variant="ghost" className="gap-2">
                  <ArrowLeftIcon className="size-4" />
                  Go Back Home
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}