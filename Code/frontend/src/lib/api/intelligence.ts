const BASE_URL = import.meta.env.VITE_API_BASE_URL

export async function getVehicleIntelligence(
    vehicleId: string,
    limit: number = 200
) {
    if (!vehicleId) throw new Error("Vehicle ID is required")

    const url = new URL(`${BASE_URL}/api/intelligence/data/all`)

    url.searchParams.append("vehicle_id", vehicleId)
    url.searchParams.append("limit", String(limit))

    const response = await fetch(url.toString())

    if (!response.ok) {
        throw new Error("Failed to fetch vehicle intelligence data")
    }

    const data = await response.json()

    // Backend returns latest → oldest
    // Reverse so charts receive oldest → latest
    return data.reverse()
}