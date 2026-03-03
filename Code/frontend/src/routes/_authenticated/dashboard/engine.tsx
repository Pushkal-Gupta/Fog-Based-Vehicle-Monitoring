import { createFileRoute } from "@tanstack/react-router"
import { useEffect } from "react"
import { useVehicle } from "@/context/vehicle-context"
import { getVehicleIntelligence } from "@/lib/api/intelligence"

export const Route = createFileRoute(
    "/_authenticated/dashboard/engine"
)({
    component: RouteComponent,
})

function RouteComponent() {
    const { selectedVehicle } = useVehicle()

    useEffect(() => {
        // if (!selectedVehicle?.vehicle_id) return

        // async function testFetch() {
        //     try {
        //         const data = await getVehicleIntelligence(
        //             selectedVehicle.vehicle_id,
        //             50
        //         )

        //         console.log("Rows:", data.length)
        //         console.log("First row:", data[0])
        //     } catch (err) {
        //         console.error(err)
        //     }
        // }

        // testFetch()
    }, [selectedVehicle])

    return (
        <div>
            Engine details for {selectedVehicle?.vehicle_id}
        </div>
    )
}