"use client"

import { Button } from "@/components/ui/button"
import { ZoomIn, ZoomOut, RotateCcw, Car } from "lucide-react"

type Props = {
    vehicleId: string
    zoomIn: () => void
    zoomOut: () => void
    reset: () => void
}

export function TwinControlsOverlay({
    vehicleId,
    zoomIn,
    zoomOut,
    reset
}: Props) {

    return (
        <div className="absolute top-4 left-4 z-20 flex items-center gap-3 bg-background/80 backdrop-blur border rounded-xl px-3 py-2 shadow-lg">

            <div className="flex items-center gap-2 pr-3 border-r">
                <Car size={16} />
                <span className="text-sm font-medium">{vehicleId}</span>
            </div>

            <Button variant="secondary" size="icon" onClick={zoomIn}>
                <ZoomIn size={16} />
            </Button>

            <Button variant="secondary" size="icon" onClick={zoomOut}>
                <ZoomOut size={16} />
            </Button>

            <Button variant="secondary" size="icon" onClick={reset}>
                <RotateCcw size={16} />
            </Button>

        </div>
    )
}