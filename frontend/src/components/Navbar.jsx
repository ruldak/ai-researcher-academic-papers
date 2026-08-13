import { Link, useNavigate } from "react-router-dom"
import { GraduationCap, LogOut } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/hooks/use-auth"

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate("/login")
  }

  return (
    <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">
      <div className="mx-auto flex h-14 w-full max-w-3xl items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-2 font-semibold">
          <GraduationCap className="h-5 w-5 text-blue-600" />
          <span>AI Researcher</span>
        </Link>
        <div className="flex items-center gap-1">
          <span className="hidden max-w-40 truncate text-sm text-muted-foreground sm:block">
            {user?.name}
          </span>
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
            <span className="hidden sm:inline">Logout</span>
          </Button>
        </div>
      </div>
    </header>
  )
}