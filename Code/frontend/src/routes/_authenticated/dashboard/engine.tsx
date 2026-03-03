import { createFileRoute } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { useVehicle } from "@/context/vehicle-context"
import { getVehicleIntelligence } from "@/lib/api/intelligence"

export const Route = createFileRoute(
    "/_authenticated/dashboard/engine"
)({
    component: RouteComponent,
})

function RouteComponent() {
    const { selectedVehicle } = useVehicle()
    const queryKey = selectedVehicle
        ? ["intelligence", selectedVehicle.vehicle_id]
        : ["intelligence", "no-vehicle"]
    const {
        data,
        isLoading,
        isError,
        error,
    } = useQuery({
        queryKey,
        queryFn: () =>
            getVehicleIntelligence(
                selectedVehicle!.vehicle_id,
                100
            ),
        enabled: !!selectedVehicle?.vehicle_id,
        refetchInterval: 5000,
        staleTime: 5000,

        // ✅ v5 replacement for keepPreviousData
        placeholderData: (previousData) => previousData,
    })

    if (!selectedVehicle) {
        return (
            <div className="flex h-[60vh] items-center justify-center text-muted-foreground text-lg">
                Select a vehicle first
            </div>
        )
    }

    if (isLoading) return <div>Loading data...</div>
    if (isError)
        return <div>Error: {(error).message}</div>

    return (
        <div className="space-y-4">
            <p>Rows fetched: {data?.length}</p>
            {/* we’ll visualize this later */}
        </div>
    )
}