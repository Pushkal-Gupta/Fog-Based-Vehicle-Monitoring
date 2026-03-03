import { createFileRoute } from "@tanstack/react-router"
import { useVehicle } from "@/context/vehicle-context"

export const Route = createFileRoute(
  "/_authenticated/dashboard/brakes"
)({
  component: BrakesPage,
})

function BrakesPage() {
  const { selectedVehicle } = useVehicle()

  if (!selectedVehicle) {
    return (
      <div className="flex h-[60vh] items-center justify-center text-muted-foreground text-lg">
        Select a vehicle first
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Brake System</h2>

      <div className="rounded-xl border p-6">
        Vehicle ID: {selectedVehicle.vehicle_id}
      </div>
    </div>
  )
}