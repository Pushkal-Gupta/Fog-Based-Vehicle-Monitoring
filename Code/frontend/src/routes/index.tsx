import { createFileRoute } from "@tanstack/react-router";
import { ComponentExample } from "@/components/component-example";

export const Route = createFileRoute("/")({ component: App });

function App() {
  return (
    <h1 className="text-center text-5xl p-10">Hello World.</h1>
  );
}