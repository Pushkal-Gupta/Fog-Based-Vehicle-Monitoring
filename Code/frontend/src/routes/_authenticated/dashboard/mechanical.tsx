"use client"

import * as React from "react"
import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ReferenceLine,
  XAxis,
  YAxis,
} from "recharts"
import type {ChartConfig} from "@/components/ui/chart";
import { useVehicle } from "@/context/vehicle-context"
import { getVehicleIntelligence } from "@/lib/api/intelligence"


import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

import {
  
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent
} from "@/components/ui/chart"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export const Route = createFileRoute(
  "/_authenticated/dashboard/mechanical"
)({
  component: MechanicalPage,
})

const chartConfig = {
  rms: {
    label: "Vibration RMS",
    color: "var(--chart-1)",
  },
  anomaly: {
    label: "Anomaly Score",
    color: "var(--chart-2)",
  },
} satisfies ChartConfig

function MechanicalPage() {
  const { selectedVehicle } = useVehicle()
  const [timeRange, setTimeRange] = React.useState("30")

  const { data, isLoading } = useQuery({
    queryKey: ["mechanical", selectedVehicle?.vehicle_id],
    queryFn: () =>
      getVehicleIntelligence(selectedVehicle!.vehicle_id, 200),
    enabled: !!selectedVehicle?.vehicle_id,
    refetchInterval: 5000,
  })

  const processedData = React.useMemo(() => {
    if (!data) return []

    const mapped = [...data].reverse().map((row) => ({
      date: new Date(Number(row.ingested_at)),
      rms: Number(row.mechanical_vibration_rms),
      anomaly: Number(row.mechanical_vibration_anomaly_score),
      freq: Number(row.mechanical_dominant_fault_band_hz),
      damping: row.fog_vibration_damping_mode_active,
    }))

    const now = mapped.at(-1)?.date
    if (!now) return mapped

    const days = Number(timeRange)
    const start = new Date(now)
    start.setDate(start.getDate() - days)

    return mapped.filter((item) => item.date >= start)
  }, [data, timeRange])

  const latest = processedData.at(-1)

  if (!selectedVehicle) {
    return (
      <div className="flex h-[60vh] items-center justify-center text-muted-foreground text-lg">
        Select a vehicle first
      </div>
    )
  }

  if (isLoading) {
    return <div className="p-6">Loading mechanical data...</div>
  }

  return (
    <div className="space-y-6 px-4 pb-10">

      {/* ================= KPI CARDS ================= */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">

        <Card>
          <CardHeader>
            <CardTitle>Vibration RMS</CardTitle>
            <CardDescription>
              Current vibration magnitude
            </CardDescription>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {latest?.rms?.toFixed(3) ?? 0}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Anomaly Score</CardTitle>
            <CardDescription>
              ML anomaly detection score
            </CardDescription>
          </CardHeader>
          <CardContent
            className={`text-3xl font-semibold ${
              latest?.anomaly > 0.7
                ? "text-red-500"
                : "text-green-500"
            }`}
          >
            {latest?.anomaly?.toFixed(3) ?? 0}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Damping Mode</CardTitle>
            <CardDescription>
              Active vibration mitigation
            </CardDescription>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {latest?.damping ? "Active" : "Inactive"}
          </CardContent>
        </Card>

      </div>

      {/* ================= INTERACTIVE CHART ================= */}
      <Card className="pt-0">
        <CardHeader className="flex items-center gap-2 space-y-0 border-b py-5 sm:flex-row">
          <div className="grid flex-1 gap-1">
            <CardTitle>Vibration Trend</CardTitle>
            <CardDescription>
              RMS levels and anomaly score over time
            </CardDescription>
          </div>

          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[140px] rounded-lg">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="rounded-xl">
              <SelectItem value="30">Last 30 days</SelectItem>
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="1">Last 24 hours</SelectItem>
            </SelectContent>
          </Select>
        </CardHeader>

        <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
          <ChartContainer
            config={chartConfig}
            className="aspect-auto h-[320px] w-full"
          >
            <AreaChart data={processedData}>
              <defs>
                <linearGradient id="fillRms" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="5%"
                    stopColor="var(--color-rms)"
                    stopOpacity={0.8}
                  />
                  <stop
                    offset="95%"
                    stopColor="var(--color-rms)"
                    stopOpacity={0.1}
                  />
                </linearGradient>
              </defs>

              <CartesianGrid vertical={false} />

              <XAxis
                dataKey="date"
                tickFormatter={(value) =>
                  new Date(value).toLocaleDateString()
                }
                tickLine={false}
                axisLine={false}
                minTickGap={32}
              />

              <YAxis />

              <ChartTooltip
                cursor={false}
                content={
                  <ChartTooltipContent
                    labelFormatter={(value) =>
                      new Date(value).toLocaleString()
                    }
                    indicator="dot"
                  />
                }
              />

              {/* Anomaly Threshold */}
              <ReferenceLine
                y={0.7}
                stroke="var(--color-anomaly)"
                strokeDasharray="4 4"
              />

              {/* RMS as Area */}
              <Area
                type="monotone"
                dataKey="rms"
                stroke="var(--color-rms)"
                fill="url(#fillRms)"
                strokeWidth={2}
              />

              {/* Anomaly as Line */}
              <Line
                type="monotone"
                dataKey="anomaly"
                stroke="var(--color-anomaly)"
                strokeWidth={3}
                dot={false}
              />

              <ChartLegend content={<ChartLegendContent />} />
            </AreaChart>
          </ChartContainer>
        </CardContent>
      </Card>

      {/* ================= TECHNICIAN PANEL ================= */}
      <Card>
        <CardHeader>
          <CardTitle>Dominant Fault Frequency</CardTitle>
          <CardDescription>
            Primary vibration fault band
          </CardDescription>
        </CardHeader>
        <CardContent className="text-3xl font-semibold">
          {latest?.freq?.toFixed(2) ?? 0} Hz
        </CardContent>
      </Card>

    </div>
  )
}