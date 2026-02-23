import { createFileRoute } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"
import { auth } from "@/lib/firebase"

export const Route = createFileRoute("/_authenticated/")({
  component: App,
})

function App() {
  return (
    <div>
      <h1 className="text-center text-5xl p-10">Hello World.</h1>
      <Button variant="destructive" onClick={() => {
        auth.signOut().then(() => {
          console.log('Signed out !');
          
        })
      }}>Click me !!</Button>
    </div>
  )
}