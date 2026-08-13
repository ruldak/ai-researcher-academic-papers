import { useQuery } from "@tanstack/react-query"
import { format } from "date-fns"
import { History } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import api from "@/lib/api"

export default function SearchHistory({ onSelect }) {
  const { data, isLoading } = useQuery({
    queryKey: ["searches"],
    queryFn: () => api.get("/searches").then((r) => r.data.searches),
  })

  if (isLoading) {
    return (
      <section>
        <h2 className="mb-3 flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <History className="h-4 w-4" /> Recent searches
        </h2>
        <div className="flex flex-col gap-2">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-14 w-full rounded-lg" />
          ))}
        </div>
      </section>
    )
  }

  if (!data?.length) {
    return (
      <p className="text-center text-sm text-muted-foreground">
        No searches yet. Start by typing a query above.
      </p>
    )
  }

  return (
    <section>
      <h2 className="mb-3 flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <History className="h-4 w-4" /> Recent searches
      </h2>
      <div className="divide-y overflow-hidden rounded-lg border bg-card">
        {data.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => onSelect(s.id)}
            className="flex w-full flex-col gap-1 px-4 py-3 text-left transition-colors hover:bg-accent/60"
          >
            <span className="text-sm font-medium leading-snug">{s.query_text}</span>
            <span className="text-xs text-muted-foreground">
              {format(new Date(s.created_at), "d MMM yyyy, HH:mm")} · {s.result_count} results
            </span>
          </button>
        ))}
      </div>
    </section>
  )
}