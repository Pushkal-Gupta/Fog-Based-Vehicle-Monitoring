"use client"

import { Html, useGLTF } from "@react-three/drei"
import { useEffect } from "react"
import { VehicleOverlay } from "./VehicleOverlay"
import type * as THREE from "three"

type Props = {
    telemetry: any
    insight: any
}

type OverlayConfig = {
    mesh: string
    title: string
    offset?: [number, number, number]
    getData: (telemetry: any, insight: any) => Record<string, any>
}

export function VehicleModel({ telemetry, insight }: Props) {

    const { scene } = useGLTF("/models/vehicle.glb")

    const overlays: Array<OverlayConfig> = [
        {
            mesh: "FL_WHEEL_1",
            title: "FL Brake",
            offset: [0, 0.35, 0],
            getData: (t) => ({
                Temp: `${t?.trigger_measured_brake_temp_c} °C`
            })
        },
        {
            mesh: "FR_WHEEL_1",
            title: "FR Brake",
            offset: [0, 0.35, 0],
            getData: (t) => ({
                Temp: `${t?.trigger_measured_brake_temp_c} °C`
            })
        },
        {
            mesh: "Exhaust",
            title: "Exhaust",
            offset: [0, 0.45, 0],
            getData: (t) => ({
                Thermal: t?.thermal_stress_index
            })
        }
    ]

    useEffect(() => {

    }, [scene])

    return (
        <primitive
            object={scene}
            scale={1.5}
            position={[0, -1, 0]}
            rotation={[0, Math.PI, 0]}
        >

            {overlays.map((overlay, i) => {

                const mesh = scene.getObjectByName(overlay.mesh)

                if (!mesh) return null

                return (
                    <group
                        key={i}
                        position={[
                            mesh.position.x,
                            mesh.position.y,
                            mesh.position.z
                        ]}
                    >
                        <Html
                            distanceFactor={8}
                            position={overlay.offset || [0, 0.3, 0]}
                        >
                            <VehicleOverlay
                                title={overlay.title}
                                data={overlay.getData(telemetry, insight)}
                            />
                        </Html>
                    </group>
                )
            })}

        </primitive>
    )
}

useGLTF.preload("/models/vehicle.glb")