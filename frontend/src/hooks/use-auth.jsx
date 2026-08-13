import { createContext, useContext, useEffect, useState } from "react"
import api from "@/lib/api"

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Cek token yang tersimpan saat aplikasi dibuka
  useEffect(() => {
    const token = localStorage.getItem("token")
    if (!token) {
      setLoading(false)
      return
    }
    api
      .get("/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => localStorage.removeItem("token"))
      .finally(() => setLoading(false))
  }, [])

  const login = async (email, password) => {
    const res = await api.post("/auth/login", { email, password })
    localStorage.setItem("token", res.data.access_token)
    setUser(res.data.user)
  }

  // Register = auto login (backend langsung mengembalikan token)
  const register = async (name, email, password) => {
    const res = await api.post("/auth/register", { name, email, password })
    localStorage.setItem("token", res.data.access_token)
    setUser(res.data.user)
  }

  const logout = () => {
    localStorage.removeItem("token")
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)