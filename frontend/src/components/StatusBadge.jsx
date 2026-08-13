import { Badge } from "@/components/ui/badge"
import { STATUSES, STATUS_BADGE_CLASSES } from "@/lib/constants"
import { cn } from "@/lib/utils"

export default function StatusBadge({ status, className }) {
  // Status default "unread" tidak ditampilkan agar list tidak berisik
  if (!status || status === "unread") return null
  const config = STATUSES.find((s) => s.value === status)

  return (
    <Badge
      variant="outline"
      className={cn("gap-1 font-normal", STATUS_BADGE_CLASSES[status], className)}
    >
      {config?.label ?? status}
    </Badge>
  )
}