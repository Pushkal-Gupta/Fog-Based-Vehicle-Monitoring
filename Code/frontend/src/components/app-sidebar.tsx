"use client"

import * as React from "react"
import {
  Activity, Battery, Car, ChevronsUpDown,
  Disc,
  Flame,
  LayoutDashboard,
  Plus,
} from "lucide-react"
import { Link, useLocation, useNavigate } from "@tanstack/react-router"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu"

import { NavUser } from "@/components/nav-user"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupAction,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar"
import { useVehicle } from "@/context/vehicle-context"

import { auth } from "@/lib/firebase"

type Vehicle = {
  vehicle_id: string
  vin: string
  dealership_name: string
  activation_status: string
  claimed_at: number
}

export function AppSidebar(props: React.ComponentProps<typeof Sidebar>) {
  const { isMobile } = useSidebar()
  const location = useLocation()
  const navigate = useNavigate()
  const [vehicles, setVehicles] = React.useState<Array<Vehicle>>([])
  const { selectedVehicle, setSelectedVehicle } = useVehicle()
  const [loading, setLoading] = React.useState(true)

  React.useEffect(() => {
    const fetchVehicles = async () => {
      try {
        const user = auth.currentUser
        if (!user) return

        const token = await user.getIdToken()

        const res = await fetch(
          `${import.meta.env.VITE_API_BASE_URL}/api/vehicle/my`,
          {
            headers: {
              authorization: `Bearer ${token}`,
            },
          }
        )

        if (!res.ok) throw new Error("Failed to fetch vehicles")

        const data = await res.json()
        setVehicles(data.vehicles || [])
      } catch (err) {
        console.error(err)
        setVehicles([])
      } finally {
        setLoading(false)
      }
    }

    fetchVehicles()
  }, [])

  const headerTitle = selectedVehicle
    ? selectedVehicle.vehicle_id
    : "No vehicle selected"

  const headerSubtitle = selectedVehicle
    ? selectedVehicle.vin
    : "Please choose a vehicle"

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton
                  size="lg"
                  className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                >
                  <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                    <Car className="size-4" />
                  </div>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-medium">
                      {headerTitle}
                    </span>
                    <span className="truncate text-xs">
                      {headerSubtitle}
                    </span>
                  </div>
                  <ChevronsUpDown className="ml-auto" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>

              <DropdownMenuContent
                className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
                align="start"
                side={isMobile ? "bottom" : "right"}
                sideOffset={4}
              >
                <DropdownMenuLabel className="text-muted-foreground text-xs">
                  Your Vehicles
                </DropdownMenuLabel>

                {loading && (
                  <DropdownMenuItem disabled>
                    Loading...
                  </DropdownMenuItem>
                )}

                {!loading && vehicles.length === 0 && (
                  <DropdownMenuItem disabled>
                    No vehicles owned
                  </DropdownMenuItem>
                )}

                {!loading &&
                  vehicles.map((vehicle, index) => (
                    <DropdownMenuItem
                      key={vehicle.vehicle_id}
                      className="gap-2 p-2"
                      onClick={() => setSelectedVehicle(vehicle)}
                    >
                      <div className="flex size-6 items-center justify-center rounded-md border">
                        <Car className="size-3.5 shrink-0" />
                      </div>

                      <div className="flex flex-col">
                        <span className="text-sm font-medium">
                          {vehicle.vehicle_id}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {vehicle.vin}
                        </span>
                      </div>

                      <DropdownMenuShortcut>
                        ⌘{index + 1}
                      </DropdownMenuShortcut>
                    </DropdownMenuItem>
                  ))}

                <DropdownMenuSeparator />

                <DropdownMenuItem className="gap-2 p-2" onClick={() => {
                  navigate({
                    to: '/claim-vehicle'
                  })
                }}>
                  <div className="flex size-6 items-center justify-center rounded-md border bg-transparent">
                    <Plus className="size-4" />
                  </div>
                  <div className="text-muted-foreground font-medium">
                    Add/Claim new vehicle.
                  </div>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Dashboard</SidebarGroupLabel>

          <SidebarGroupContent>
            <SidebarMenu>

              {/* Overview */}
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={location.pathname === "/dashboard"}
                >
                  <Link to="/dashboard">
                    <LayoutDashboard />
                    <span>Overview</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>

              {/* Engine */}
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={location.pathname.startsWith("/dashboard/engine")}
                >
                  <Link to="/dashboard/engine">
                    <Flame />
                    <span>Engine</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>

              {/* Brakes */}
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={location.pathname.startsWith("/dashboard/brakes")}
                >
                  <Link to="/dashboard/brakes">
                    <Disc />
                    <span>Brakes</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>

              {/* Mechanical */}
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={location.pathname.startsWith("/dashboard/mechanical")}
                >
                  <Link to="/dashboard/mechanical">
                    <Activity />
                    <span>Mechanical</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>

              {/* Electrical */}
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={location.pathname.startsWith("/dashboard/electrical")}
                >
                  <Link to="/dashboard/electrical">
                    <Battery />
                    <span>Electrical</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>


              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  className="bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
                >
                  <Link to="/dashboard/digital-twin">
                    <Car />
                    <span>Digital Twin</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <NavUser
          user={{
            name: auth.currentUser?.displayName || "User",
            email: auth.currentUser?.email || "user@example.com",
            avatar: auth.currentUser?.photoURL || undefined,
          }}
        />
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  )
}