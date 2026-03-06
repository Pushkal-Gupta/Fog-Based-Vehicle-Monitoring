import { createFileRoute } from "@tanstack/react-router"
import { VehicleCanvas } from "@/components/digital-twin/vehicle-canvas"
import { useVehicle } from "@/context/vehicle-context"

export const Route = createFileRoute(
  "/_authenticated/dashboard/digital-twin"
)({
  component: DigitalTwinPage,
})

function DigitalTwinPage() {
  const { selectedVehicle } = useVehicle()

  if (!selectedVehicle) {
    return (
      <div className="flex h-[60vh] items-center justify-center text-muted-foreground text-lg">
        Select a vehicle first
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6 h-full">

      {/* Header */}
      <div>
        <h2 className="text-2xl font-semibold">Vehicle Digital Twin</h2>
        <p className="text-sm text-muted-foreground">
          Interactive real-time visualization of vehicle systems
        </p>
      </div>

      {/* 3D Scene Container */}
      <div className="flex-1 min-h-[600px] rounded-xl border overflow-hidden">
        <VehicleCanvas vehicleId={selectedVehicle.vehicle_id} />
      </div>

    </div>
  )
}