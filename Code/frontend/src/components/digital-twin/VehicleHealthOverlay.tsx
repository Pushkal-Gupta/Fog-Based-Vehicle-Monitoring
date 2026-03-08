"use client"

import { Progress } from "@/components/ui/progress"

type Props = {
    score: number
}

export function VehicleHealthOverlay({ score }: Props) {

    const color =
        score > 80
            ? "bg-green-500"
            : score > 60
                ? "bg-yellow-500"
                : "bg-red-500"

    return (
        <div className="
        absolute
        bottom-6
        left-1/2
        -translate-x-1/2
        z-20
        w-9/12
        rounded-lg
        border
        bg-background/10
        backdrop-blur
        px-4
        py-3
        shadow
    ">

            <div className="flex justify-between text-sm font-medium mb-2">
                <span>Vehicle Health</span>
                <span>{score}%</span>
            </div>

            <Progress
                value={score}
                className={`h-3 ${color}`}
            />

        </div>
    )
}