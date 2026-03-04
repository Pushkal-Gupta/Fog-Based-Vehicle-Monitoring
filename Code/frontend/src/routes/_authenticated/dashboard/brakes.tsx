import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { useMemo } from "react"
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts"
import { useVehicle } from "@/context/vehicle-context"
import { getVehicleIntelligence } from "@/lib/api/intelligence"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"


export const Route = createFileRoute(
  "/_authenticated/dashboard/brakes"
)({
  component: BrakesPage,
})

function BrakesPage() {
  const { selectedVehicle } = useVehicle()

  const queryKey = selectedVehicle
    ? ["intelligence-brakes", selectedVehicle.vehicle_id]
    : ["intelligence-brakes", "no-vehicle"]

  const { data, isLoading, isError, error } = useQuery({
    queryKey,
    queryFn: () =>
      getVehicleIntelligence(selectedVehicle!.vehicle_id, 100),
    enabled: !!selectedVehicle?.vehicle_id,
    refetchInterval: 5000,
    staleTime: 5000,
    placeholderData: (previousData) => previousData,
  })

  const processedSeries = useMemo(() => {
    if (!data) return []

    return [...data].reverse().map((row) => ({
      time: Number(row.timestamp_ms),
      temp: Number(row.trigger_measured_brake_temp_c),
      rise: Number(row.trigger_brake_temp_rise_rate),
      margin: Number(row.thermal_brake_margin),
      rul: Number(row.brake_rul_pct),
    }))
  }, [data])

  const latest = processedSeries.at(-1)
  const latestRow = data?.[0]

  const latestTemp = latest?.temp ?? 0
  const latestRUL = latest?.rul ?? 0
  const latestMargin = latest?.margin ?? 0

  const getHealthStatus = (rul: number) => {
    if (rul > 70) return { label: "Healthy", color: "text-green-500" }
    if (rul > 40) return { label: "Degrading", color: "text-yellow-500" }
    return { label: "Critical", color: "text-red-500" }
  }

  const health = getHealthStatus(latestRUL)

  if (!selectedVehicle) {
    return (
      <div className="flex h-[60vh] items-center justify-center text-muted-foreground text-lg px-4 text-center">
        Select a vehicle first
      </div>
    )
  }

  if (isLoading) return <div className="px-4">Loading data...</div>

  if (isError) {
    return (
      <div className="px-4">
        Error: {(error)?.message ?? "Unknown error"}
      </div>
    )
  }

  return (
    <div className="space-y-6 px-4 pb-10">

      {/* ================= KPI SECTION ================= */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-2xl border p-5">
          <p className="text-sm text-muted-foreground">
            Brake RUL
          </p>
          <p className="text-2xl sm:text-3xl font-semibold">
            {latestRUL.toFixed(2)}%
          </p>
          <p className={`text-sm font-medium ${health.color}`}>
            {health.label}
          </p>
        </div>

        <div className="rounded-2xl border p-5">
          <p className="text-sm text-muted-foreground">
            Current Brake Temperature
          </p>
          <p className="text-2xl sm:text-3xl font-semibold">
            {latestTemp.toFixed(1)} °C
          </p>
        </div>

        <div className="rounded-2xl border p-5">
          <p className="text-sm text-muted-foreground">
            Service Required
          </p>
          <p className="text-2xl sm:text-3xl font-semibold">
            {latestRow?.fog_predictive_service_required
              ? "Yes"
              : "No"}
          </p>
        </div>
      </div>

      {/* ================= MAIN CHART ================= */}
      <div className="rounded-2xl border p-4 sm:p-6">
        <ChartContainer
          config={{
            temp: {
              label: "Brake Temperature (°C)",
              color: "#ef4444",
            },
            rise: {
              label: "Temp Rise Rate",
              color: "#3b82f6",
            },
          }}
        >
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={processedSeries}>
              <defs>
                <linearGradient id="fillTemp" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.05} />
                </linearGradient>

                <linearGradient id="fillRise" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.05} />
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" />

              <XAxis
                dataKey="time"
                tickFormatter={(value) =>
                  new Date(Number(value)).toLocaleTimeString()
                }
                minTickGap={20}
              />

              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" width={50} />

              <ChartTooltip
                content={
                  <ChartTooltipContent
                    labelFormatter={(value) =>
                      new Date(Number(value)).toLocaleTimeString()
                    }
                    indicator="dot"
                  />
                }
              />

              <Area
                yAxisId="left"
                type="monotone"
                dataKey="temp"
                stroke="#ef4444"
                fill="url(#fillTemp)"
                strokeWidth={2}
                dot={false}
              />

              <Area
                yAxisId="right"
                type="monotone"
                dataKey="rise"
                stroke="#3b82f6"
                fill="url(#fillRise)"
                strokeWidth={2}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>

      {/* ================= THERMAL RISK PANEL ================= */}
      <div className="rounded-2xl border p-6 space-y-4">
        <h3 className="text-lg font-semibold">
          Thermal Risk Status
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">
              Thermal Brake Margin:
            </span>{" "}
            <span
              className={
                latestMargin < 0
                  ? "text-red-500 font-medium"
                  : "text-green-500 font-medium"
              }
            >
              {latestMargin.toFixed(3)}
            </span>
          </div>

          <div>
            <span className="text-muted-foreground">
              Stress Mitigation Active:
            </span>{" "}
            {latestRow?.fog_brake_stress_mitigation_active
              ? "Yes"
              : "No"}
          </div>

          <div>
            <span className="text-muted-foreground">
              AI Confidence:
            </span>{" "}
            {(
              (latestRow?.fog_decision_confidence ?? 0) * 100
            ).toFixed(1)}
            %
          </div>
        </div>
      </div>
    </div>
  )
}