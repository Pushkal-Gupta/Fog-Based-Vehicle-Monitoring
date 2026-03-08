"use client"

import { Canvas, useFrame } from "@react-three/fiber"
import { Grid, OrbitControls } from "@react-three/drei"
import { useRef } from "react"
import { VehicleModel } from "./vehicle-model"
import { VehicleHealthOverlay } from "./VehicleHealthOverlay"
import { TwinControlsOverlay } from "./TwinControlsOverlay"
import type * as THREE from "three"
import { useDigitalTwinData } from "@/hooks/useDigitalTwinData"

type Props = {
    vehicleId: string
}

// NeonGrid component for animated effect
function NeonGrid({ parentRef }: { parentRef: React.RefObject<THREE.Group> }) {
    const gridRef = useRef<any>(null)

    useFrame((state, delta) => {
        if (!gridRef.current || !parentRef.current) return

        // Scroll forward effect
        gridRef.current.position.z += delta * 2
        if (gridRef.current.position.z > 0) {
            gridRef.current.position.z = -60
        }

        // Match rotation of parent (vehicle) so grid rotates with it
        gridRef.current.rotation.y = parentRef.current.rotation.y
    })

    return (
        <Grid
            ref={gridRef}
            position={[0, -1.1, -30]} // start slightly behind
            args={[60, 60]}           // large grid
            cellSize={0.2}
            cellThickness={0.5}
            sectionSize={3}
            sectionThickness={1}
            fadeDistance={250}
            fadeStrength={1}
            infiniteGrid
            color="#0ff"              // neon cyan
            sectionColor="#0ff"
            cellColor="#0ff"
            lineWidth={1.2}
        />
    )
}

export function VehicleCanvas({ vehicleId }: Props) {

    const { data } = useDigitalTwinData(vehicleId)
    const controlsRef = useRef<any>(null)
    const groupRef = useRef<THREE.Group>(null) // vehicle + grid parent

    if (!data) return null

    const zoomIn = () => {
        if (!controlsRef.current) return
        controlsRef.current.object.position.z -= 0.8
        controlsRef.current.update()
    }

    const zoomOut = () => {
        if (!controlsRef.current) return
        controlsRef.current.object.position.z += 0.8
        controlsRef.current.update()
    }

    const resetCamera = () => {
        if (!controlsRef.current) return
        controlsRef.current.object.position.set(4, 2, 6)
        controlsRef.current.target.set(0, 0, 0)
        controlsRef.current.update()
    }

    return (
        <div className="relative h-full w-full rounded-xl border overflow-hidden">

            {/* UI overlay OUTSIDE canvas */}
            <TwinControlsOverlay
                vehicleId={vehicleId}
                zoomIn={zoomIn}
                zoomOut={zoomOut}
                reset={resetCamera}
            />

            <Canvas camera={{ position: [4, 2, 6], fov: 50 }}>

                {/* Scene-wide fog */}
                <fog attach="fog" args={[0x000000, 10, 50]} />

                <ambientLight intensity={0.6} />
                <directionalLight position={[5, 5, 5]} intensity={1} />

                {/* Group parent for vehicle + grid */}
                <group ref={groupRef}>

                    {/* Animated neon grid that rotates with vehicle */}
                    <NeonGrid parentRef={groupRef} />

                    {/* Vehicle model */}
                    <VehicleModel
                        telemetry={data.telemetry}
                        insight={data.insight}
                    />

                </group>

                <OrbitControls
                    ref={controlsRef}
                    enableZoom
                    enableRotate
                    enablePan
                />

            </Canvas>

            {/* Floating health bar */}
            <VehicleHealthOverlay
                score={data.telemetry.vehicle_health_score}
            />

        </div>
    )
}