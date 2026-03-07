"use client"

import { Html, Line, useGLTF } from "@react-three/drei"
import * as THREE from "three"
import { useEffect } from "react"
import { VehicleOverlay } from "./VehicleOverlay"

type Props = {
    telemetry: any
    insight: any
}

type OverlayStatus = "normal" | "warning" | "critical"

type OverlayConfig = {
    mesh: string
    title: string
    anchorOffset: [number, number, number]
    boxOffset: [number, number, number]
    getData: (telemetry: any, insight: any) => Record<string, any>
    getStatus?: (telemetry: any, insight: any) => OverlayStatus
}

function getMeshCenter(mesh: THREE.Object3D) {
    const box = new THREE.Box3().setFromObject(mesh)
    const center = new THREE.Vector3()
    box.getCenter(center)
    return center
}

export function VehicleModel({ telemetry, insight }: Props) {

    const { scene } = useGLTF("/models/vehicle.glb")

    useEffect(() => {
        console.log("---- GLB MESH LIST ----")

        scene.traverse((child) => {
            if (child instanceof THREE.Mesh) {
                console.log(child.name)
            }
        })

        console.log("---- END MESH LIST ----")
    }, [scene])

    const overlays: Array<OverlayConfig> = [

        // FRONT LEFT BRAKE
        {
            mesh: "FL_WHEEL_1",
            title: "Front Left Brake",

            anchorOffset: [-1.6, 0.1, 0],
            boxOffset: [-2.2, 1.2, 0],

            getStatus: (t) => {
                const temp = t?.trigger_measured_brake_temp_c || 0
                if (temp > 350) return "critical"
                if (temp > 250) return "warning"
                return "normal"
            },

            getData: (t) => ({
                Temp: `${t?.trigger_measured_brake_temp_c?.toFixed(1)} °C`,
                RiseRate: `${t?.trigger_brake_temp_rise_rate?.toFixed(3)}`,
                RUL: `${t?.brake_rul_pct}%`
            })
        },

        // FRONT RIGHT BRAKE
        {
            mesh: "FR_WHEEL_1",
            title: "Front Right Brake",

            anchorOffset: [1.6, 0.1, 0],
            boxOffset: [2.2, 1.2, 0],

            getStatus: (t) => {
                const temp = t?.trigger_measured_brake_temp_c || 0
                if (temp > 350) return "critical"
                if (temp > 250) return "warning"
                return "normal"
            },

            getData: (t) => ({
                Temp: `${t?.trigger_measured_brake_temp_c?.toFixed(1)} °C`,
                RiseRate: `${t?.trigger_brake_temp_rise_rate?.toFixed(3)}`,
                RUL: `${t?.brake_rul_pct}%`
            })
        },

        // ENGINE / POWERTRAIN
        {
            mesh: "Bottom",
            title: "Engine / Powertrain",

            anchorOffset: [0, -0.1, 2],
            boxOffset: [0, 1.8, 1.8],

            getStatus: (t) => {
                if (t?.thermal_stress_index > 0.8) return "warning"
                return "normal"
            },

            getData: (t) => ({
                ThermalStress: `${t?.thermal_stress_index}`,
                EngineMargin: `${t?.thermal_engine_margin}`,
                EngineRUL: `${t?.engine_rul_pct}%`,
                Health: `${t?.vehicle_health_score}`
            })
        },

        // MECHANICAL VIBRATION
        {
            mesh: "Bottom",
            title: "Mechanical System",

            anchorOffset: [0, 0.2, -0.3],
            boxOffset: [-2.3, 1.3, -1.2],

            getStatus: (t) => {
                if (t?.mechanical_vibration_anomaly_score > 0.7) return "warning"
                return "normal"
            },

            getData: (t) => ({
                RMS: `${t?.mechanical_vibration_rms?.toFixed(3)}`,
                Anomaly: `${t?.mechanical_vibration_anomaly_score}`,
                FaultBand: `${t?.mechanical_dominant_fault_band_hz?.toFixed(1)} Hz`
            })
        },

        // BATTERY SYSTEM
        {
            mesh: "Bottom",
            title: "Battery System",

            anchorOffset: [0, 0.2, 0],
            boxOffset: [2.3, 1.3, -0.8],

            getStatus: (t) => {
                const health = t?.electrical_battery_health_pct || 100
                if (health < 40) return "critical"
                if (health < 60) return "warning"
                return "normal"
            },

            getData: (t) => ({
                Health: `${t?.electrical_battery_health_pct?.toFixed(1)}%`,
                ChargeEfficiency: `${t?.electrical_charging_efficiency_score}`,
                BatteryRUL: `${t?.battery_rul_pct}%`
            })
        },

        // AI DECISION LAYER
        {
            mesh: "Bottom",
            title: "AI Decision Layer",

            anchorOffset: [0, 0.8, 0],
            boxOffset: [0, 2.2, 0],

            getStatus: (t) => {
                if (t?.fog_decision_critical_class === 1) return "critical"
                return "normal"
            },

            getData: (t) => ({
                CriticalClass: `${t?.fog_decision_critical_class}`,
                Confidence: `${(t?.fog_decision_confidence * 100).toFixed(1)}%`,
                Actuation: t?.fog_decision_actuation_triggered ? "ON" : "OFF"
            })
        },

        // SAFETY SYSTEMS
        {
            mesh: "Bottom",
            title: "Safety Systems",

            anchorOffset: [0, 0.5, -1],
            boxOffset: [0, 1.8, -2.3],

            getStatus: (t) => {
                if (t?.fog_emergency_safeguard_active) return "critical"
                if (t?.fog_brake_stress_mitigation_active) return "warning"
                return "normal"
            },

            getData: (t) => ({
                ThermalProtection: t?.fog_thermal_protection_active ? "ON" : "OFF",
                BrakeMitigation: t?.fog_brake_stress_mitigation_active ? "ON" : "OFF",
                VibrationDamping: t?.fog_vibration_damping_mode_active ? "ON" : "OFF",
                Emergency: t?.fog_emergency_safeguard_active ? "ON" : "OFF"
            })
        }

    ]

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

                const center = getMeshCenter(mesh)

                const start = center.clone().add(
                    new THREE.Vector3(...overlay.anchorOffset)
                )

                const end = center.clone().add(
                    new THREE.Vector3(...overlay.boxOffset)
                )

                const mid = start.clone().lerp(end, 0.4)

                const data = overlay.getData(telemetry, insight)

                const status = overlay.getStatus
                    ? overlay.getStatus(telemetry, insight)
                    : "normal"

                return (
                    <group key={i}>

                        <Line
                            points={[
                                [start.x, start.y, start.z],
                                [mid.x, mid.y, mid.z],
                                [end.x, end.y, end.z]
                            ]}
                            color="white"
                            lineWidth={1.5}
                        />

                        <Html
                            position={[end.x, end.y, end.z]}
                            distanceFactor={6}
                        >
                            <VehicleOverlay
                                title={overlay.title}
                                data={data}
                                status={status}
                            />
                        </Html>

                    </group>
                )

            })}
        </primitive>
    )
}

useGLTF.preload("/models/vehicle.glb")