"use client"

import * as React from "react"
import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  XAxis,
  YAxis,
} from "recharts"
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
  "/_authenticated/dashboard/electrical"
)({
  component: ElectricalPage,
})

const chartConfig = {
  health: {
    label: "Battery Health %",
    color: "var(--chart-1)",
  },
  efficiency: {
    label: "Charging Efficiency %",
    color: "var(--chart-2)",
  },
} satisfies ChartConfig

function ElectricalPage() {
  const { selectedVehicle } = useVehicle()
  const [timeRange, setTimeRange] = React.useState("90")

  const { data, isLoading } = useQuery({
    queryKey: ["battery", selectedVehicle?.vehicle_id],
    queryFn: () =>
      getVehicleIntelligence(selectedVehicle!.vehicle_id, 200),
    enabled: !!selectedVehicle?.vehicle_id,
    refetchInterval: 5000,
  })

  const processedData = React.useMemo(() => {
    if (!data) return []

    const mapped = [...data].reverse().map((row) => ({
      date: new Date(Number(row.ingested_at)),
      health: Number(row.electrical_battery_health_pct),
      efficiency:
        Number(row.electrical_charging_efficiency_score) * 100,
      rul: Number(row.battery_rul_pct),
    }))

    const now = mapped.at(-1)?.date
    if (!now) return mapped

    const days = Number(timeRange)
    const start = new Date(now)
    start.setDate(start.getDate() - days)

    return mapped.filter((item) => item.date >= start)
  }, [data, timeRange])

  if (!selectedVehicle) {
    return (
      <div className="flex h-[60vh] items-center justify-center text-muted-foreground text-lg">
        Select a vehicle first
      </div>
    )
  }

  if (isLoading) {
    return <div className="p-6">Loading battery data...</div>
  }

  return (
    <div className="space-y-6 px-4 pb-10">

      {/* ================= KPI CARDS ================= */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Battery Health</CardTitle>
            <CardDescription>Current condition</CardDescription>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {processedData.at(-1)?.health?.toFixed(1) ?? 0}%
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Battery RUL</CardTitle>
            <CardDescription>Remaining useful life</CardDescription>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {processedData.at(-1)?.rul?.toFixed(1) ?? 0}%
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Charging Efficiency</CardTitle>
            <CardDescription>Current efficiency</CardDescription>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {processedData.at(-1)?.efficiency?.toFixed(1) ?? 0}%
          </CardContent>
        </Card>
      </div>

      {/* ================= INTERACTIVE CHART ================= */}
      <Card className="pt-0">
        <CardHeader className="flex items-center gap-2 space-y-0 border-b py-5 sm:flex-row">
          <div className="grid flex-1 gap-1">
            <CardTitle>Battery Performance Trend</CardTitle>
            <CardDescription>
              Health degradation and charging efficiency
            </CardDescription>
          </div>

          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[140px] rounded-lg">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="rounded-xl">
              <SelectItem value="90">Last 90 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
              <SelectItem value="7">Last 7 days</SelectItem>
            </SelectContent>
          </Select>
        </CardHeader>

        <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
          <ChartContainer
            config={chartConfig}
            className="aspect-auto h-80 w-full"
          >
            <AreaChart data={processedData}>
              <defs>
                <linearGradient id="fillHealth" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="5%"
                    stopColor="var(--color-health)"
                    stopOpacity={0.8}
                  />
                  <stop
                    offset="95%"
                    stopColor="var(--color-health)"
                    stopOpacity={0.1}
                  />
                </linearGradient>
              </defs>

              <CartesianGrid vertical={false} />

              <XAxis
                dataKey="date"
                tickFormatter={(value) =>
                  new Date(value).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                  })
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
                      new Date(value).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                      })
                    }
                    indicator="dot"
                  />
                }
              />

              {/* Battery Health Area */}
              <Area
                type="monotone"
                dataKey="health"
                stroke="var(--color-health)"
                fill="url(#fillHealth)"
                strokeWidth={2}
              />

              {/* Charging Efficiency Line */}
              <Line
                type="monotone"
                dataKey="efficiency"
                stroke="var(--color-efficiency)"
                strokeWidth={3}
                dot={false}
              />

              <ChartLegend content={<ChartLegendContent />} />
            </AreaChart>
          </ChartContainer>
        </CardContent>
      </Card>
    </div>
  )
}