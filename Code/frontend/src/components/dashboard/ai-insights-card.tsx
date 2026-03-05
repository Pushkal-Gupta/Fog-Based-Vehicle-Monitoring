"use client"

import { useQuery } from "@tanstack/react-query"
import {
  Activity,
  AlertTriangle,
  Brain,
  Flame,
  ShieldAlert,
  Wrench
} from "lucide-react"
import { useEffect, useState } from "react"
import { useVehicle } from "@/context/vehicle-context"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card"

async function getAIInsight(vehicleId: string) {
  const BASE_URL = import.meta.env.VITE_API_BASE_URL
  const res = await fetch(`${BASE_URL}/api/insights/latest_ai_insight/${vehicleId}`)
  return res.json()
}

export function AIInsightCards() {
  const { selectedVehicle } = useVehicle()
  const [secondsAgo, setSecondsAgo] = useState(0)

  // Query to fetch AI insights
  const { data, dataUpdatedAt } = useQuery({
    queryKey: ["ai-insight", selectedVehicle?.vehicle_id],
    queryFn: () => getAIInsight(selectedVehicle!.vehicle_id),
    enabled: !!selectedVehicle?.vehicle_id,
    refetchInterval: 8000,
  })

  // Update "seconds ago" every second
  useEffect(() => {
    const interval = setInterval(() => {
      if (dataUpdatedAt) {
        const diff = Math.floor((Date.now() - dataUpdatedAt) / 1000)
        setSecondsAgo(diff)
      }
    }, 1000)
    return () => clearInterval(interval)
  }, [dataUpdatedAt])

  // Early return if data not loaded yet
  if (!data) return null

  const critical = data.recommendation_service_priority === "critical"
  const service = data.recommendation_service_priority === "service"
  const thermalProtect = data.thermal_protection_active
  const emergency = data.emergency_safeguard_active
  const recommendationText = data.recommendation_suggested_action

  return (
    <Card className="relative overflow-hidden border-8 border-green-900/20">

      {/* Mesh Gradient Background */}
      <div
        className="absolute inset-0 -z-10"
        style={{
          backgroundColor: "hsla(262,10%,16%,1)",
          backgroundImage: `
            radial-gradient(at 71% 15%, hsla(209,19%,7%,1) 0px, transparent 50%),
            radial-gradient(at 24% 79%, hsla(347,10%,1%,1) 0px, transparent 50%),
            radial-gradient(at 13% 16%, hsla(204,41%,15%,1) 0px, transparent 50%)
          `
        }}
      />

      <CardHeader className="flex flex-row items-start justify-between">

        {/* LEFT SIDE */}
        <div className="flex items-center gap-3">
          <Brain className="w-6 h-6 text-primary" />
          <div>
            <CardTitle>Fog AI Health Status</CardTitle>
            <CardDescription>
              Edge AI predictive diagnostics and protection monitoring
            </CardDescription>
          </div>
        </div>

        {/* RIGHT SIDE: Last updated */}
        <div className="text-xs text-muted-foreground whitespace-nowrap">
          Last updated {secondsAgo === 0 ? "just now" : `${secondsAgo}s ago`}
        </div>

      </CardHeader>

      <CardContent className="space-y-6">

        {/* Top Analytics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

          <Card className={`p-5 ${critical ? "bg-red-500/10 border-red-500/30" : "bg-green-500/10 border-green-500/30"}`}>
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 mt-1" />
              <div>
                <p className="text-sm text-muted-foreground">Critical Classification</p>
                <p className="text-xl font-semibold">{critical ? "Critical Condition" : "Normal Condition"}</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Fog AI engine health classification based on vibration, temperature and harmonic analysis.
                </p>
              </div>
            </div>
          </Card>

          <Card className={`p-5 ${service ? "bg-yellow-500/10 border-yellow-500/30" : "bg-green-500/10 border-green-500/30"}`}>
            <div className="flex items-start gap-3">
              <Wrench className="w-6 h-6 mt-1" />
              <div>
                <p className="text-sm text-muted-foreground">Service Requirement</p>
                <p className="text-xl font-semibold">{service ? "Maintenance Required" : "No Service Needed"}</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Predictive maintenance indicator derived from abnormal operational signatures.
                </p>
              </div>
            </div>
          </Card>

          <Card className={`p-5 ${thermalProtect ? "bg-orange-500/10 border-orange-500/30" : "bg-green-500/10 border-green-500/30"}`}>
            <div className="flex items-start gap-3">
              <Flame className="w-6 h-6 mt-1" />
              <div>
                <p className="text-sm text-muted-foreground">Thermal Protection</p>
                <p className="text-xl font-semibold">{thermalProtect ? "Protection Active" : "Temperature Normal"}</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Thermal safeguard triggered when engine heat approaches operational safety limits.
                </p>
              </div>
            </div>
          </Card>

        </div>

        {/* Recommended Action Card */}
        <Card className={`p-6 ${critical ? "bg-red-500/10 border-red-500/30" : service ? "bg-yellow-500/10 border-yellow-500/30" : "bg-green-500/10 border-green-500/30"}`}>
          <div className="flex items-start gap-3">
            {critical ? <ShieldAlert className="w-7 h-7 mt-1" /> : <Activity className="w-7 h-7 mt-1" />}
            <div>
              <p className="text-sm text-muted-foreground">Recommended Action</p>
              <p className="text-2xl font-semibold mt-1">
                {critical ? "Immediate Shutdown Recommended" : service ? "Service Inspection Advised" : "Vehicle Operating Normally"}
              </p>
              <p className="text-base mt-2 text-muted-foreground leading-relaxed">{recommendationText}</p>

              <div className="mt-3 text-sm text-muted-foreground">
                <p className="font-medium text-foreground mb-1">Contributing Factors</p>
                <ul className="list-disc pl-5 space-y-1">
                  {thermalProtect && <li>Elevated engine temperature triggering thermal safeguard</li>}
                  {service && <li>Detected abnormal vibration or harmonic pattern</li>}
                  {critical && <li>Fog AI classified engine health as critical</li>}
                  {emergency && <li>Emergency protection system activated</li>}
                  {!thermalProtect && !service && !critical && <li>No abnormal conditions detected</li>}
                </ul>
              </div>
            </div>
          </div>
        </Card>

      </CardContent>
    </Card>
  )
}