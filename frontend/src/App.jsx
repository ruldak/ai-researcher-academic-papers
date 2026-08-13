import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Toaster } from "sonner"
import { AuthProvider } from "@/hooks/use-auth"
import ProtectedRoute from "@/components/ProtectedRoute"
import Layout from "@/components/Layout"
import LoginPage from "@/pages/LoginPage"
import RegisterPage from "@/pages/RegisterPage"
import SearchPage from "@/pages/SearchPage"
import ResultsPage from "@/pages/ResultsPage"
import PaperDetailPage from "@/pages/PaperDetailPage"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<SearchPage />} />
              <Route path="/results/:searchId" element={<ResultsPage />} />
              <Route path="/papers/:paperId" element={<PaperDetailPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <Toaster position="top-center" richColors closeButton />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}