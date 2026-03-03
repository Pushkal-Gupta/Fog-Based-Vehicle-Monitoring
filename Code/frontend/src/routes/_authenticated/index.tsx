import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export const Route = createFileRoute("/_authenticated/")({
  component: AuthHome,
})

function AuthHome() {
  const navigate = useNavigate()

  return (
    <div className="flex items-center justify-center min-h-screen p-6">
      <Card className="w-full max-w-md shadow-xl rounded-2xl">
        <CardHeader>
          <CardTitle className="text-2xl text-center">
            Welcome
          </CardTitle>
        </CardHeader>

        <CardContent className="flex justify-center">
          <Button
            size="lg"
            className="w-full text-lg"
            onClick={() => navigate({ to: "/dashboard" })}
          >
            Go to Dashboard
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}