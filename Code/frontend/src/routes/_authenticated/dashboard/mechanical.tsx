import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { useMemo } from "react"
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
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
  "/_authenticated/dashboard/mechanical"
)({
  component: MechanicalPage,
})

function MechanicalPage() {
  const { selectedVehicle } = useVehicle()

  const queryKey = selectedVehicle
    ? ["intelligence-mech", selectedVehicle.vehicle_id]
    : ["intelligence-mech", "no-vehicle"]

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
      rms: Number(row.mechanical_vibration_rms),
      anomaly: Number(row.mechanical_vibration_anomaly_score),
      freq: Number(row.mechanical_dominant_fault_band_hz),
    }))
  }, [data])

  const latest = processedSeries.at(-1)
  const latestRow = data?.[0]

  const latestRMS = latest?.rms ?? 0
  const latestAnomaly = latest?.anomaly ?? 0
  const latestFreq = latest?.freq ?? 0

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
        Error: {(error).message}
      </div>
    )
  }

  return (
    <div className="space-y-6 px-4 pb-10">

      {/* ================= KPI SECTION ================= */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-2xl border p-5">
          <p className="text-sm text-muted-foreground">
            Vibration RMS
          </p>
          <p className="text-2xl sm:text-3xl font-semibold">
            {latestRMS.toFixed(3)}
          </p>
        </div>

        <div className="rounded-2xl border p-5">
          <p className="text-sm text-muted-foreground">
            Anomaly Score
          </p>
          <p
            className={`text-2xl sm:text-3xl font-semibold ${latestAnomaly > 0.7
                ? "text-red-500"
                : "text-green-500"
              }`}
          >
            {latestAnomaly.toFixed(3)}
          </p>
        </div>

        <div className="rounded-2xl border p-5">
          <p className="text-sm text-muted-foreground">
            Damping Mode Active
          </p>
          <p className="text-2xl sm:text-3xl font-semibold">
            {latestRow?.fog_vibration_damping_mode_active
              ? "Yes"
              : "No"}
          </p>
        </div>
      </div>

      {/* ================= MAIN CHART ================= */}
      <div className="rounded-2xl border p-4 sm:p-6">
        <ChartContainer
          config={{
            rms: {
              label: "Vibration RMS",
              color: "#8b5cf6",
            },
            anomaly: {
              label: "Anomaly Score",
              color: "#ef4444",
            },
          }}
        >
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={processedSeries}>
              <CartesianGrid strokeDasharray="3 3" />

              <XAxis
                dataKey="time"
                tickFormatter={(value) =>
                  new Date(Number(value)).toLocaleTimeString()
                }
                minTickGap={20}
              />

              <YAxis />

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

              {/* Anomaly Threshold */}
              <ReferenceLine
                y={0.7}
                stroke="#ef4444"
                strokeDasharray="5 5"
              />

              <Area
                type="monotone"
                dataKey="rms"
                stroke="#8b5cf6"
                fill="#8b5cf6"
                fillOpacity={0.2}
                strokeWidth={2}
                dot={false}
              />

              <Area
                type="monotone"
                dataKey="anomaly"
                stroke="#ef4444"
                fill="#ef4444"
                fillOpacity={0.2}
                strokeWidth={2}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>

      {/* ================= TECHNICIAN PANEL ================= */}
      <div className="rounded-2xl border p-6 space-y-4">
        <h3 className="text-lg font-semibold">
          Dominant Fault Frequency
        </h3>

        <p className="text-2xl font-semibold">
          {latestFreq.toFixed(2)} Hz
        </p>
      </div>
    </div>
  )
}