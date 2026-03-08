"use client"

import {
    Card,
    CardHeader,
    CardTitle,
    CardContent
} from "@/components/ui/card"

import { Badge } from "@/components/ui/badge"

type Props = {
    title: string
    data: Record<string, any>
    status?: "normal" | "warning" | "critical"
}

export function VehicleOverlay({
    title,
    data,
    status = "normal"
}: Props) {

    const statusStyle =
        status === "critical"
            ? "border-red-500 shadow-[0_0_12px_rgba(239,68,68,0.8)]"
            : status === "warning"
                ? "border-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.7)]"
                : "border-border"

    const badgeVariant =
        status === "critical"
            ? "destructive"
            : status === "warning"
                ? "secondary"
                : "outline"

    return (
        <Card
            className={`
        w-[170px]
        text-xs
        bg-background/20
        backdrop-blur
        border
        py-1
        ${statusStyle}
      `}
        >

            <CardHeader className="flex flex-row items-center justify-between p-2 pb-0">

                <CardTitle className="text-[11px] font-semibold">
                    {title}
                </CardTitle>

                <Badge variant={badgeVariant} className="text-[9px]">
                    {status}
                </Badge>

            </CardHeader>

            <CardContent className="p-2 pt-0 pt-1 space-y-[3px]">

                {Object.entries(data).map(([k, v]) => (

                    <div key={k} className="flex justify-between">

                        <span className="text-muted-foreground">
                            {k}
                        </span>

                        <span className="font-medium">
                            {v}
                        </span>

                    </div>

                ))}

            </CardContent>

        </Card>
    )
}