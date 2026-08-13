import { BookOpen, CheckCircle2, Circle, SkipForward } from "lucide-react"

export const STATUSES = [
  { value: "unread", label: "Unread", icon: Circle },
  { value: "reading", label: "Reading", icon: BookOpen },
  { value: "reviewed", label: "Reviewed", icon: CheckCircle2 },
  { value: "skipped", label: "Skipped", icon: SkipForward },
]

// Badge kecil di card hasil pencarian
export const STATUS_BADGE_CLASSES = {
  unread: "border-slate-200 bg-slate-100 text-slate-600 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-300",
  reading: "border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-900 dark:bg-blue-950 dark:text-blue-300",
  reviewed: "border-green-200 bg-green-50 text-green-700 dark:border-green-900 dark:bg-green-950 dark:text-green-300",
  skipped: "border-orange-200 bg-orange-50 text-orange-700 dark:border-orange-900 dark:bg-orange-950 dark:text-orange-300",
}

// Tombol aktif di halaman detail
export const STATUS_ACTIVE_CLASSES = {
  unread: "border-slate-600 bg-slate-600 text-white hover:bg-slate-700 hover:text-white",
  reading: "border-blue-600 bg-blue-600 text-white hover:bg-blue-700 hover:text-white",
  reviewed: "border-green-600 bg-green-600 text-white hover:bg-green-700 hover:text-white",
  skipped: "border-orange-500 bg-orange-500 text-white hover:bg-orange-600 hover:text-white",
}