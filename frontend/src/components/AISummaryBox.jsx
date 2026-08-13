import { Sparkles } from "lucide-react"

export default function AISummaryBox({ summary }) {
  // ai_summary bisa null → sembunyikan box
  if (!summary) return null

  return (
    <div className="rounded-lg border border-blue-100 bg-blue-50 p-4 dark:border-blue-900 dark:bg-blue-950/40">
      <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
        <Sparkles className="h-4 w-4" />
        <h2 className="text-sm font-semibold">AI Summary</h2>
      </div>
      <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-slate-700 dark:text-slate-300">
        {summary}
      </p>
    </div>
  )
}