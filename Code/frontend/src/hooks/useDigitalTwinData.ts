import { useQuery } from "@tanstack/react-query"

const BASE_URL = import.meta.env.VITE_API_BASE_URL

async function fetchTelemetry(vehicleId: string) {
  const res = await fetch(
    `${BASE_URL}/api/intelligence/data/all?vehicle_id=${vehicleId}&limit=1`
  )

  if (!res.ok) throw new Error("Telemetry fetch failed")

  const data = await res.json()

  return data[0]
}

async function fetchAIInsight(vehicleId: string) {
  const res = await fetch(
    `${BASE_URL}/api/insights/latest_ai_insight/${vehicleId}`
  )

  if (!res.ok) throw new Error("AI insight fetch failed")

  return res.json()
}

export function useDigitalTwinData(vehicleId: string) {
  return useQuery({
    queryKey: ["digital-twin-data", vehicleId],
    queryFn: async () => {
      const [telemetry, insight] = await Promise.all([
        fetchTelemetry(vehicleId),
        fetchAIInsight(vehicleId),
      ])

      return {
        telemetry,
        insight,
      }
    },
    refetchInterval: 5000,
    enabled: !!vehicleId,
  })
}