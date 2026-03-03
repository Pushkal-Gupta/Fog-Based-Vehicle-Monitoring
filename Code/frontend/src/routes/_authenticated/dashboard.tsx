
import { Outlet, createFileRoute, useLocation } from "@tanstack/react-router"
import { AppSidebar } from "@/components/app-sidebar"
import { VehicleProvider } from "@/context/vehicle-context"
import { getVehicleIntelligence } from "@/lib/api/intelligence"

import {
    SidebarInset,
    SidebarProvider,
    SidebarTrigger,
} from "@/components/ui/sidebar"

export const Route = createFileRoute('/_authenticated/dashboard')({
    component: DashboardLayout,
})

function DashboardLayout() {
    const location = useLocation()

    const getTitle = () => {
        const path = location.pathname

        if (path === "/dashboard") return "Overview"
        if (path.startsWith("/dashboard/engine")) return "Engine Analytics"
        if (path.startsWith("/dashboard/brakes")) return "Brake Analytics"
        if (path.startsWith("/dashboard/mechanical")) return "Mechanical / Vibration"
        if (path.startsWith("/dashboard/electrical")) return "Electrical / Battery"

        return "Vehicle Dashboard"
    }

    return (
        <VehicleProvider>
            <SidebarProvider>
                <AppSidebar />

                <SidebarInset>
                    {/* Header */}
                    <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
                        <SidebarTrigger className="-ml-1" />
                        <h1 className="font-semibold">{getTitle()}</h1>
                    </header>

                    {/* Page Content */}
                    <div className="flex flex-1 flex-col p-4">
                        <Outlet />
                    </div>
                </SidebarInset>
            </SidebarProvider>
        </VehicleProvider>

    )
}