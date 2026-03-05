"use client"
import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import {
  Label,
  PolarGrid,
  PolarRadiusAxis,
  RadialBar,
  RadialBarChart,
} from "recharts"
import { AIInsightCards, AIInsightSidebar } from "../../../components/dashboard/ai-insights-card"
import type { ChartConfig } from "@/components/ui/chart";
import { useVehicle } from "@/context/vehicle-context"
import { getVehicleIntelligence } from "@/lib/api/intelligence"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

import { ChartContainer } from "@/components/ui/chart"
import { Separator } from "@base-ui/react"

export const Route = createFileRoute(
  "/_authenticated/dashboard/"
)({
  component: DashboardPage,
})

function DashboardPage() {
  const { selectedVehicle } = useVehicle()
  const getHealthColor = (value: number) => {
    if (value > 70) return "#22c55e"      // green-500
    if (value > 40) return "#facc15"      // yellow-400
    return "#ef4444"                      // red-500
  }
  
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard-latest", selectedVehicle?.vehicle_id],
    queryFn: async () => {
      const res = await getVehicleIntelligence(
        selectedVehicle!.vehicle_id,
        1
      )
      return res[0] // only latest row
    },
    enabled: !!selectedVehicle?.vehicle_id,
    refetchInterval: 5000, // poll every 5s
  })

  if (!selectedVehicle) {
    return (
      <div className="flex h-[60vh] items-center justify-center text-muted-foreground text-lg">
        Select a vehicle first
      </div>
    )
  }

  if (isLoading || !data) {
    return <div className="p-6">Loading dashboard...</div>
  }

  const gauges = [
    {
      label: "Engine Health",
      value: Number(data.engine_rul_pct ?? 0),
    },
    {
      label: "Brake Health",
      value: Number(data.brake_rul_pct ?? 0),
    },
    {
      label: "Battery Health",
      value: Number(data.battery_rul_pct ?? 0),
    },
    {
      label: "Vehicle Score",
      value: Number(data.vehicle_health_score ?? 0),
    },
  ]

  const flags = [
    {
      title: "Thermal Protection Active",
      active: data.fog_thermal_protection_active,
      description:
        "Engine thermal protection is limiting performance to prevent overheating damage.",
    },
    {
      title: "Brake Stress Mitigation",
      active: data.fog_brake_stress_mitigation_active,
      description:
        "Brake system stress control is adjusting braking force distribution.",
    },
    {
      title: "Vibration Damping Mode",
      active: data.fog_vibration_damping_mode_active,
      description:
        "Active vibration suppression is engaged to stabilize mechanical stress.",
    },
    {
      title: "Predictive Service Required",
      active: data.fog_predictive_service_required,
      description:
        "AI model predicts upcoming component degradation requiring maintenance.",
    },
    {
      title: "Emergency Safeguard Active",
      active: data.fog_emergency_safeguard_active,
      description:
        "Critical protection mode activated due to severe anomaly detection.",
    },
  ]

  return (
    <div className="flex flex-col xl:flex-row gap-6 px-4 pb-10">

      {/* MAIN DASHBOARD */}
      <div className="flex-1 space-y-8">
        <AIInsightCards />
        
        <h3 className="font-medium">Live Vehicle Data</h3>
        {/* ================= RADIAL GAUGES ================= */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {gauges.map((gauge) => {
            const color = getHealthColor(gauge.value)

            const chartData = [
              {
                name: gauge.label,
                value: gauge.value,
                fill: color,
              },
            ]

            const chartConfig = {
              value: {
                label: gauge.label,
                color: color,
              },
            } satisfies ChartConfig

            return (
              <Card key={gauge.label} className="flex flex-col">
                <CardHeader className="items-center pb-0">
                  <CardTitle>{gauge.label}</CardTitle>
                  <CardDescription>
                    Current health percentage
                  </CardDescription>
                </CardHeader>

                <CardContent className="flex-1 pb-6">
                  <ChartContainer
                    config={chartConfig}
                    className="mx-auto aspect-square max-h-55"
                  >
                    <RadialBarChart
                      data={chartData}
                      startAngle={180}
                      endAngle={0}
                      innerRadius={70}
                      outerRadius={110}
                    >
                      <PolarGrid
                        gridType="circle"
                        radialLines={false}
                        stroke="none"
                        className="first:fill-muted last:fill-background"
                        polarRadius={[76, 64]}
                      />

                      <RadialBar
                        dataKey="value"
                        cornerRadius={10}
                        fill={color}
                        background
                      />

                      <PolarRadiusAxis
                        tick={false}
                        tickLine={false}
                        axisLine={false}
                        domain={[0, 100]}
                      >
                        <Label
                          content={({ viewBox }) => {
                            if (viewBox && "cx" in viewBox) {
                              return (
                                <text
                                  x={viewBox.cx}
                                  y={viewBox.cy}
                                  textAnchor="middle"
                                  dominantBaseline="middle"
                                >
                                  <tspan
                                    x={viewBox.cx}
                                    y={viewBox.cy}
                                    className="text-3xl font-bold"
                                    fill={color}
                                  >
                                    {gauge.value.toFixed(0)}%
                                  </tspan>
                                  <tspan
                                    x={viewBox.cx}
                                    y={viewBox.cy + 20}
                                    className="font-bold"
                                    fill="#fff"
                                  >
                                    LOW
                                  </tspan>
                                </text>
                              )
                            }
                          }}
                        />
                      </PolarRadiusAxis>
                    </RadialBarChart>
                  </ChartContainer>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* ================= FLAG STATUS ================= */}
        <Card>
          <CardHeader>
            <CardTitle>Fog Control & Protection Status</CardTitle>
            <CardDescription>
              Active mitigation and predictive safety mechanisms
            </CardDescription>
          </CardHeader>

          <CardContent className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {flags.map((flag) => (
              <Card key={flag.title} className="p-4">
                <CardHeader className="p-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {flag.title}
                  </CardTitle>
                </CardHeader>

                <CardContent className="p-0 space-y-2">
                  <div
                    className={`text-base font-semibold ${flag.active
                      ? "text-red-500"
                      : "text-green-500"
                      }`}
                  >
                    {flag.active ? "Active" : "Inactive"}
                  </div>

                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {flag.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}