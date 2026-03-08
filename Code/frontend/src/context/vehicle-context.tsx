import React from "react"

export type Vehicle = {
    vehicle_id: string
    vin: string
    dealership_name: string
    activation_status: string
    claimed_at: number
}

type VehicleContextType = {
    selectedVehicle: Vehicle | null
    setSelectedVehicle: (v: Vehicle | null) => void
}

const VehicleContext = React.createContext<VehicleContextType | null>(null)

export function VehicleProvider({ children }: { children: React.ReactNode }) {
    const [selectedVehicle, setSelectedVehicle] =
        React.useState<Vehicle | null>(null)

    return (
        <VehicleContext.Provider value={{ selectedVehicle, setSelectedVehicle }}>
            {children}
        </VehicleContext.Provider>
    )
}

export function useVehicle() {
    const ctx = React.useContext(VehicleContext)
    if (!ctx) throw new Error("useVehicle must be used inside VehicleProvider")
    return ctx
}