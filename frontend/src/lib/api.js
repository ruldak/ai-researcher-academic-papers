import axios from "axios"

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
})

// Kirim token di setiap request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token")
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 401 → token expired/invalid → redirect ke login
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token")
      const path = window.location.pathname
      if (path !== "/login" && path !== "/register") {
        window.location.href = "/login"
      }
    }
    return Promise.reject(error)
  }
)

// Ambil pesan error dari backend (string detail atau array validasi 422)
export function getErrorMessage(error, fallback = "Something went wrong") {
  const detail = error?.response?.data?.detail
  if (typeof detail === "string") return detail
  if (Array.isArray(detail) && detail.length > 0) return detail[0]?.msg || fallback
  return fallback
}

export default api