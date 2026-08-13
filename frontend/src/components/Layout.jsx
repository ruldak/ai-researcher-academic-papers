import { Outlet } from "react-router-dom"
import Navbar from "@/components/Navbar"

export default function Layout() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="mx-auto w-full max-w-3xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}