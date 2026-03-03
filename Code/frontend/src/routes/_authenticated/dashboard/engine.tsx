import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { useVehicle } from "@/context/vehicle-context"
import { getVehicleIntelligence } from "@/lib/api/intelligence"
import { useMemo } from "react"

import {
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
    ChartLegend,
    ChartLegendContent,
} from "@/components/ui/chart"

import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    ResponsiveContainer,
} from "recharts"

export const Route = createFileRoute(
    "/_authenticated/dashboard/engine"
)({
    component: RouteComponent,
})

function RouteComponent() {
    const { selectedVehicle } = useVehicle()

    const queryKey = selectedVehicle
        ? ["intelligence", selectedVehicle.vehicle_id]
        : ["intelligence", "no-vehicle"]

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
            rul: Number(row.engine_rul_pct),
            stress: Number(row.thermal_stress_index),
        }))
    }, [data])

    const latest = processedSeries.at(-1)
    const latestRow = data?.[0]

    const latestRUL = latest?.rul ?? 0
    const latestStress = latest?.stress ?? 0

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
                Error: {(error as Error)?.message ?? "Unknown error"}
            </div>
        )
    }

    return (
        <div className="space-y-6 px-4 pb-10">

            {/* ================= KPI SECTION ================= */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="rounded-2xl border p-5">
                    <p className="text-sm text-muted-foreground">
                        Latest Engine RUL
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
                        Thermal Stress Index
                    </p>
                    <p className="text-2xl sm:text-3xl font-semibold text-red-500">
                        {latestStress.toFixed(2)}
                    </p>
                </div>

                <div className="rounded-2xl border p-5">
                    <p className="text-sm text-muted-foreground">
                        AI Confidence
                    </p>
                    <p className="text-2xl sm:text-3xl font-semibold">
                        {(
                            (latestRow?.fog_decision_confidence ?? 0) * 100
                        ).toFixed(1)}
                        %
                    </p>
                </div>
            </div>

            {/* ================= AREA CHART ================= */}
            <div className="rounded-2xl border p-4 sm:p-6">
                <ChartContainer
                    config={{
                        rul: {
                            label: "Engine RUL %",
                            color: "var(--chart-1)",
                        },
                        stress: {
                            label: "Thermal Stress",
                            color: "var(--chart-2)",
                        },
                    }}
                >
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={processedSeries}>

                            {/* Gradient Definitions */}
                            <defs>
                                <linearGradient id="fillRUL" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="var(--color-rul)" stopOpacity={0.8} />
                                    <stop offset="95%" stopColor="var(--color-rul)" stopOpacity={0.1} />
                                </linearGradient>

                                <linearGradient id="fillStress" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="var(--color-stress)" stopOpacity={0.9} />
                                    <stop offset="95%" stopColor="var(--color-stress)" stopOpacity={0.1} />
                                </linearGradient>
                            </defs>

                            <CartesianGrid vertical={false} />

                            <XAxis
                                dataKey="time"
                                tickFormatter={(value) =>
                                    new Date(Number(value)).toLocaleTimeString()
                                }
                                minTickGap={30}
                                tickMargin={8}
                            />

                            <YAxis yAxisId="left" domain={[0, 100]} />
                            <YAxis
                                yAxisId="right"
                                orientation="right"
                                width={40}
                            />

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
                                dataKey="rul"
                                stroke="var(--color-rul)"
                                fill="url(#fillRUL)"
                                strokeWidth={2}
                            />

                            <Area
                                yAxisId="right"
                                type="monotone"
                                dataKey="stress"
                                stroke="var(--color-stress)"
                                fill="url(#fillStress)"
                                strokeWidth={2}
                            />

                            <ChartLegend content={<ChartLegendContent />} />

                        </AreaChart>
                    </ResponsiveContainer>
                </ChartContainer>
            </div>

            {/* ================= AI PANEL ================= */}
            <div className="rounded-2xl border p-6 space-y-4">
                <h3 className="text-lg font-semibold">Fog AI Status</h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                    <div>
                        <span className="text-muted-foreground">
                            Critical Class:
                        </span>{" "}
                        {latestRow?.fog_decision_critical_class === 1 ? "Yes" : "No"}
                    </div>

                    <div>
                        <span className="text-muted-foreground">
                            Predictive Service Required:
                        </span>{" "}
                        {latestRow?.fog_predictive_service_required ? "Yes" : "No"}
                    </div>

                    <div>
                        <span className="text-muted-foreground">
                            Thermal Protection Active:
                        </span>{" "}
                        {latestRow?.fog_thermal_protection_active ? "Yes" : "No"}
                    </div>

                    <div>
                        <span className="text-muted-foreground">
                            Emergency Safeguard Active:
                        </span>{" "}
                        {latestRow?.fog_emergency_safeguard_active ? "Yes" : "No"}
                    </div>
                </div>
            </div>
        </div>
    )
}