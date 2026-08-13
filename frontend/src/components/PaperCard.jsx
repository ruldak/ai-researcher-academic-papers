import { Link } from "react-router-dom"
import { BarChart3 } from "lucide-react"
import StatusBadge from "@/components/StatusBadge"
import TypeBadge from "@/components/TypeBadge"
import OABadge from "@/components/OABadge"

export default function PaperCard({ paper }) {
  const authorsText = paper.authors?.length ? paper.authors.join(", ") : "Unknown authors"

  return (
    <Link
      to={`/papers/${paper.id}`}
      className="block rounded-lg border bg-card p-4 transition-colors hover:border-blue-300 hover:bg-accent/40"
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-semibold leading-snug">{paper.title}</h3>
        <StatusBadge status={paper.status} className="shrink-0" />
      </div>

      <p className="mt-1.5 truncate text-sm text-muted-foreground">{authorsText}</p>

      <div className="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-muted-foreground">
        <span className="font-medium text-foreground/80">{paper.publication_year}</span>
        <TypeBadge type={paper.type} />
        {paper.is_oa && <OABadge />}
        <span className="inline-flex items-center gap-1">
          <BarChart3 className="h-3.5 w-3.5" />
          {paper.cited_by_count ?? 0}
        </span>
        {paper.source_name && <span className="truncate">{paper.source_name}</span>}
      </div>
    </Link>
  )
}