import { Canvas } from "@react-three/fiber"
import { OrbitControls } from "@react-three/drei"
import { VehicleModel } from "./vehicle-model"
import { useDigitalTwinData } from "@/hooks/useDigitalTwinData"

type Props = {
    vehicleId: string
}

export function VehicleCanvas({ vehicleId }: Props) {

    const { data } = useDigitalTwinData(vehicleId)

    if (!data) return null

    return (
        <div className="h-[600px] w-full rounded-xl border">

            <Canvas camera={{ position: [4, 2, 6], fov: 50 }}>

                <ambientLight intensity={0.6} />
                <directionalLight position={[5, 5, 5]} intensity={1} />

                <VehicleModel
                    telemetry={data.telemetry}
                    insight={data.insight}
                />

                <OrbitControls enableZoom enableRotate enablePan />

            </Canvas>

        </div>
    )
}