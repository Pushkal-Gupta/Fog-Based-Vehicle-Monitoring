import { createFileRoute } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"

export const Route = createFileRoute("/_authenticated/")({
  component: App,
})

function App() {
  return (
    <div>
      <h1 className="text-center text-5xl p-10">Hello World.</h1>
      <Button variant="destructive">Click me !!</Button>
    </div>
  )
}