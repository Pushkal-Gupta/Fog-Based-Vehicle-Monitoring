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
    "/_authenticated/dashboard/engine"
)({
    component: EnginePage,
})

const chartConfig = {
    rul: {
        label: "Engine RUL %",
        color: "var(--chart-1)",
    },
    stress: {
        label: "Thermal Stress Index",
        color: "var(--chart-2)",
    },
} satisfies ChartConfig

function EnginePage() {
    const { selectedVehicle } = useVehicle()
    const [timeRange, setTimeRange] = React.useState("7")

    const { data, isLoading } = useQuery({
        queryKey: ["engine", selectedVehicle?.vehicle_id],
        queryFn: () =>
            getVehicleIntelligence(selectedVehicle!.vehicle_id, 200),
        enabled: !!selectedVehicle?.vehicle_id,
        refetchInterval: 5000,
    })

    const processedData = React.useMemo(() => {
        if (!data) return []

        const mapped = [...data].reverse().map((row) => ({
            date: new Date(Number(row.timestamp_ms)),
            rul: Number(row.engine_rul_pct),
            stress: Number(row.thermal_stress_index),
            confidence: row.fog_decision_confidence,
            critical: row.fog_decision_critical_class === 1,
            service: row.fog_predictive_service_required,
            thermalProtect: row.fog_thermal_protection_active,
            emergency: row.fog_emergency_safeguard_active,
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
        return <div className="p-6">Loading engine data...</div>
    }

    return (
        <div className="space-y-6 px-4 pb-10">

            {/* ================= KPI CARDS ================= */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">

                <Card>
                    <CardHeader>
                        <CardTitle>Engine RUL</CardTitle>
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
                        <CardTitle>Thermal Stress Index</CardTitle>
                        <CardDescription>
                            Real-time thermal loading factor
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="text-3xl font-semibold text-red-500">
                        {latest?.stress?.toFixed(2) ?? 0}
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>AI Confidence</CardTitle>
                        <CardDescription>
                            Fog inference certainty
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="text-3xl font-semibold">
                        {((latest?.confidence ?? 0) * 100).toFixed(1)}%
                    </CardContent>
                </Card>

            </div>

            {/* ================= INTERACTIVE CHART ================= */}
            <Card className="pt-0">
                <CardHeader className="flex items-center gap-2 space-y-0 border-b py-5 sm:flex-row">
                    <div className="grid flex-1 gap-1">
                        <CardTitle>Engine Health Trend</CardTitle>
                        <CardDescription>
                            RUL percentage and thermal stress over time
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
                                <linearGradient id="fillRul" x1="0" y1="0" x2="0" y2="1">
                                    <stop
                                        offset="5%"
                                        stopColor="var(--color-rul)"
                                        stopOpacity={0.8}
                                    />
                                    <stop
                                        offset="95%"
                                        stopColor="var(--color-rul)"
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

                            <YAxis domain={[0, 100]} />

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

                            {/* Critical RUL threshold */}
                            <ReferenceLine
                                y={40}
                                stroke="var(--color-stress)"
                                strokeDasharray="4 4"
                            />

                            {/* RUL Area */}
                            <Area
                                type="monotone"
                                dataKey="rul"
                                stroke="var(--color-rul)"
                                fill="url(#fillRul)"
                                strokeWidth={2}
                            />

                            {/* Stress Line */}
                            <Line
                                type="monotone"
                                dataKey="stress"
                                stroke="var(--color-stress)"
                                strokeWidth={3}
                                dot={false}
                            />

                            <ChartLegend content={<ChartLegendContent />} />
                        </AreaChart>
                    </ChartContainer>
                </CardContent>
            </Card>

            {/* ================= FOG AI PANEL ================= */}
            <Card>
                <CardHeader>
                    <CardTitle>Fog AI Status</CardTitle>
                    <CardDescription>
                        Engine protection & predictive flags
                    </CardDescription>
                </CardHeader>

                <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">

                    <Card className="p-4">
                        <CardHeader className="p-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                Critical Class
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-0 text-base font-semibold">
                            {latest?.critical ? (
                                <span className="text-red-500">Yes</span>
                            ) : (
                                <span className="text-green-500">No</span>
                            )}
                        </CardContent>
                    </Card>

                    <Card className="p-4">
                        <CardHeader className="p-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                Service Required
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-0 text-base font-semibold">
                            {latest?.service ? (
                                <span className="text-yellow-500">Yes</span>
                            ) : (
                                <span className="text-green-500">No</span>
                            )}
                        </CardContent>
                    </Card>

                    <Card className="p-4">
                        <CardHeader className="p-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                Thermal Protection
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-0 text-base font-semibold">
                            {latest?.thermalProtect ? "Active" : "Inactive"}
                        </CardContent>
                    </Card>

                    <Card className="p-4">
                        <CardHeader className="p-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                Emergency Safeguard
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-0 text-base font-semibold">
                            {latest?.emergency ? "Active" : "Inactive"}
                        </CardContent>
                    </Card>

                </CardContent>
            </Card>

        </div>
    )
}