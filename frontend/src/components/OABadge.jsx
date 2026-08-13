import { LockOpen } from "lucide-react"
import { Badge } from "@/components/ui/badge"

export default function OABadge() {
  return (
    <Badge
      variant="outline"
      className="gap-1 border-green-200 bg-green-50 font-normal text-green-700 dark:border-green-900 dark:bg-green-950 dark:text-green-400"
    >
      <LockOpen className="h-3 w-3" /> Open Access
    </Badge>
  )
}