import { Badge } from "@/components/ui/badge"

const LABELS = {
  article: "Article",
  review: "Review",
  preprint: "Preprint",
  "book-chapter": "Book Chapter",
  book: "Book",
  "conference-paper": "Conference Paper",
  "conference-abstract": "Conference Abstract",
  "book-review": "Book Review",
  thesis: "Thesis",
  dataset: "Dataset",
  report: "Report",
  letter: "Letter",
  erratum: "Erratum",
  paratext: "Paratext",
}

export default function TypeBadge({ type }) {
  if (!type) return null
  return (
    <Badge variant="secondary" className="font-normal">
      {LABELS[type] ?? type}
    </Badge>
  )
}