"use client"

import { useState } from "react"
import { createFileRoute } from "@tanstack/react-router"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Field,
  FieldGroup,
  FieldLabel,
  FieldDescription,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { ButtonGroup } from "@/components/ui/button-group"

export const Route = createFileRoute("/admin")({
  component: AdminPage,
})

function AdminPage() {
  const [vehicleId, setVehicleId] = useState("")
  const [vin, setVin] = useState("")
  const [dealership, setDealership] = useState("")
  const [adminKey, setAdminKey] = useState("supersecret123")
  const [loading, setLoading] = useState(false)
  const [responseData, setResponseData] = useState<any>(null)

  // 🚗 Random Generators
  const generateVehicleId = () => {
    const random = Math.random().toString(36).substring(2, 8).toUpperCase()
    return `VEH-${random}`
  }

  const generateVIN = () => {
    const chars = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789" // no I,O,Q
    let result = ""
    for (let i = 0; i < 17; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return result
  }
  const handleCopyActivation = async (code: string) => {
    try {
      await navigator.clipboard.writeText(code)
      toast.success("Activation code copied to clipboard 📋")
    } catch {
      toast.error("Failed to copy activation code.")
    }
  }
  const handleGenerate = async () => {
    if (!vehicleId || !vin || !dealership || !adminKey) {
      toast.error("All fields are required.")
      return
    }

    try {
      setLoading(true)

      const res = await fetch(
        "https://fog-based-vehicle-monitoring.onrender.com/api/vehicle/generate_vehicle",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "x-admin-key": adminKey,
          },
          body: JSON.stringify({
            vehicle_id: vehicleId,
            vin: vin,
            dealership_name: dealership,
          }),
        }
      )

      if (!res.ok) {
        const error = await res.json()

        toast.error(error?.detail || "Failed to generate vehicle.")
        return
      }

      const data = await res.json()
      setResponseData(data)
      toast.success("Vehicle generated successfully 🚗")

    } catch (error) {
      toast.error("Server error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-8">
      <h1 className="text-3xl font-bold">Admin Vehicle Generator</h1>

      <Card>
        <CardHeader>
          <CardTitle>Generate Vehicle</CardTitle>
        </CardHeader>
        <CardContent>
          <FieldGroup className="space-y-4">

            <div className="flex justify-end">
            </div>

            <Field >
              <FieldLabel>Vehicle ID</FieldLabel>
              <ButtonGroup>
                <Input
                  value={vehicleId}
                  onChange={(e) => setVehicleId(e.target.value)}
                  placeholder="VEH-XXXXXX"
                />
                <Button onClick={() => {
                  setVehicleId(generateVehicleId())
                }}>Randomize.</Button>
              </ButtonGroup>

            </Field>
            <Field>
              <FieldLabel>VIN</FieldLabel>
              <ButtonGroup>
                <Input
                  value={vin}
                  onChange={(e) => setVin(e.target.value)}
                  placeholder="17 character VIN"
                />
                <Button onClick={() => {
                  setVin(generateVIN())
                }}>Randomize</Button>
              </ButtonGroup>

            </Field>

            <Field>
              <FieldLabel>Dealership Name</FieldLabel>
              <Input
                value={dealership}
                onChange={(e) => setDealership(e.target.value)}
                placeholder="Chennai Motors"
              />
            </Field>

            <Field>
              <FieldLabel>Admin Secret Key</FieldLabel>
              <Input
                type="password"
                value={adminKey}
                onChange={(e) => setAdminKey(e.target.value)}
                placeholder="Enter admin key"
              />
              <FieldDescription>
                Sent as x-admin-key header
              </FieldDescription>
            </Field>

            <Button onClick={handleGenerate} disabled={loading}>
              {loading ? "Generating..." : "Generate Vehicle"}
            </Button>

          </FieldGroup>
        </CardContent>
      </Card>

      {responseData && (
        <Card className="border-green-500">
          <CardHeader>
            <CardTitle>
              <div className="flex gap-1 flex-col">
                <p className="opacity-50">Vehicle ID</p>
                <h3 className="scroll-m-20 text-xl font-semibold tracking-tight">{responseData.vehicle_id}</h3>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">

            <p className="text-center opacity-60 font-semibold">
              Activation Code
            </p>
            <h1
              onClick={() => handleCopyActivation(responseData.activation_code)}
              className="scroll-m-20 text-center text-9xl font-extrabold tracking-tight cursor-pointer hover:opacity-80 transition active:scale-95 select-none"
              title="Click to copy"
            >
              {responseData.activation_code}
            </h1>
          </CardContent>
        </Card>
      )}


    </div>
  )
}