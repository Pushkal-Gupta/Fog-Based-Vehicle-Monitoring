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
import type { ChartConfig } from "@/components/ui/chart"

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
  ChartTooltipContent,
} from "@/components/ui/chart"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export const Route = createFileRoute(
  "/_authenticated/dashboard/brakes"
)({
  component: BrakesPage,
})

const chartConfig = {
  temp: {
    label: "Brake Temperature (°C)",
    color: "var(--chart-1)",
  },
  rise: {
    label: "Temp Rise Rate",
    color: "var(--chart-2)",
  },
} satisfies ChartConfig

function BrakesPage() {
  const { selectedVehicle } = useVehicle()
  const [timeRange, setTimeRange] = React.useState("7")

  const { data, isLoading } = useQuery({
    queryKey: ["brakes", selectedVehicle?.vehicle_id],
    queryFn: () =>
      getVehicleIntelligence(selectedVehicle!.vehicle_id, 200),
    enabled: !!selectedVehicle?.vehicle_id,
    refetchInterval: 5000,
  })

  const processedData = React.useMemo(() => {
    if (!data) return []

    const mapped = [...data].reverse().map((row) => ({
      date: new Date(Number(row.timestamp_ms)),
      temp: Number(row.trigger_measured_brake_temp_c),
      rise: Number(row.trigger_brake_temp_rise_rate),
      margin: Number(row.thermal_brake_margin),
      rul: Number(row.brake_rul_pct),
      mitigation: row.fog_brake_stress_mitigation_active,
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
    return <div className="p-6">Loading brake data...</div>
  }

  return (
    <div className="space-y-6 px-4 pb-10">

      {/* ================= KPI CARDS ================= */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">

        <Card>
          <CardHeader>
            <CardTitle>Brake RUL</CardTitle>
            <CardDescription>
              Remaining useful life percentage
            </CardDescription>
          </CardHeader>
          <CardContent
            className={`text-3xl font-semibold ${latest?.rul > 70
                ? "text-green-500"
                : latest?.rul > 40
                  ? "text-yellow-500"
                  : "text-red-500"
              }`}
          >
            {latest?.rul?.toFixed(2) ?? 0}%
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Brake Temperature</CardTitle>
            <CardDescription>
              Current measured disc temperature
            </CardDescription>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {latest?.temp?.toFixed(1) ?? 0} °C
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Mitigation Mode</CardTitle>
            <CardDescription>
              Thermal stress mitigation status
            </CardDescription>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {latest?.mitigation ? "Active" : "Inactive"}
          </CardContent>
        </Card>

      </div>

      {/* ================= INTERACTIVE CHART ================= */}
      <Card className="pt-0">
        <CardHeader className="flex items-center gap-2 space-y-0 border-b py-5 sm:flex-row">
          <div className="grid flex-1 gap-1">
            <CardTitle>Brake Thermal Trend</CardTitle>
            <CardDescription>
              Temperature and rise-rate behaviour over time
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
                <linearGradient id="fillTemp" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="5%"
                    stopColor="var(--color-temp)"
                    stopOpacity={0.8}
                  />
                  <stop
                    offset="95%"
                    stopColor="var(--color-temp)"
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

              {/* Critical temperature threshold example */}
              <ReferenceLine
                y={400}
                stroke="var(--color-rise)"
                strokeDasharray="4 4"
              />

              {/* Temperature as Area */}
              <Area
                type="monotone"
                dataKey="temp"
                stroke="var(--color-temp)"
                fill="url(#fillTemp)"
                strokeWidth={2}
              />

              {/* Rise Rate as Line */}
              <Line
                type="monotone"
                dataKey="rise"
                stroke="var(--color-rise)"
                strokeWidth={3}
                dot={false}
              />

              <ChartLegend content={<ChartLegendContent />} />
            </AreaChart>
          </ChartContainer>
        </CardContent>
      </Card>

      {/* ================= THERMAL PANEL ================= */}
      <Card>
        <CardHeader>
          <CardTitle>Thermal Brake Margin</CardTitle>
          <CardDescription>
            Remaining thermal safety margin
          </CardDescription>
        </CardHeader>
        <CardContent
          className={`text-3xl font-semibold ${latest?.margin < 0 ? "text-red-500" : "text-green-500"
            }`}
        >
          {latest?.margin?.toFixed(3) ?? 0}
        </CardContent>
      </Card>

    </div>
  )
}