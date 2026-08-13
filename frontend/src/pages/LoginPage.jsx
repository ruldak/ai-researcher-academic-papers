import { useForm } from "react-hook-form"
import { Link, Navigate, useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { GraduationCap, Loader2, NotebookPen, Library, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from "@/hooks/use-auth"
import { getErrorMessage } from "@/lib/api"

export default function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm()

  if (user) return <Navigate to="/" replace />

  const onSubmit = async (values) => {
    try {
      await login(values.email, values.password)
      toast.success("Welcome back!")
      navigate("/")
    } catch (err) {
      toast.error(getErrorMessage(err, "Invalid email or password"))
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-muted/40 px-4 py-10">
      {/* Brand */}
      <div className="mb-6 flex flex-col items-center text-center">
        <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 text-white">
          <GraduationCap className="h-6 w-6" />
        </div>
        <h1 className="text-xl font-semibold">AI Researcher</h1>
        <p className="mt-1 max-w-xs text-sm text-muted-foreground">
          Search academic papers, get AI summaries, and keep track of your reading.
        </p>
      </div>

      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-lg">Login</CardTitle>
          <CardDescription>Sign in to continue your research</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                autoComplete="email"
                {...register("email", { required: "Email is required" })}
              />
              {errors.email && <p className="text-xs text-red-600">{errors.email.message}</p>}
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                autoComplete="current-password"
                {...register("password", { required: "Password is required" })}
              />
              {errors.password && <p className="text-xs text-red-600">{errors.password.message}</p>}
            </div>

            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Login
            </Button>
          </form>

          <p className="mt-4 text-center text-sm text-muted-foreground">
            Don't have an account?{" "}
            <Link to="/register" className="font-medium text-blue-600 hover:underline">
              Register
            </Link>
          </p>
        </CardContent>
      </Card>

      {/* Value proposition singkat */}
      <div className="mt-6 flex w-full max-w-sm flex-wrap items-center justify-center gap-x-5 gap-y-2 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1.5"><Sparkles className="h-3.5 w-3.5" /> AI summaries</span>
        <span className="inline-flex items-center gap-1.5"><Library className="h-3.5 w-3.5" /> Reading statuses</span>
        <span className="inline-flex items-center gap-1.5"><NotebookPen className="h-3.5 w-3.5" /> Personal notes</span>
      </div>
    </div>
  )
}