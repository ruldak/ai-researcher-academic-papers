import { useState } from "react"
import { SlidersHorizontal, X } from "lucide-react"

export const DOCUMENT_TYPES = [
  { value: "", label: "All types" },
  { value: "article", label: "Article" },
  { value: "review", label: "Review" },
  { value: "conference-paper", label: "Conference Paper" },
  { value: "conference-abstract", label: "Conference Abstract" },
  { value: "preprint", label: "Preprint" },
  { value: "book", label: "Book" },
  { value: "book-chapter", label: "Book Chapter" },
  { value: "book-review", label: "Book Review" },
  { value: "thesis", label: "Thesis" },
  { value: "dataset", label: "Dataset" },
  { value: "report", label: "Report" },
  { value: "letter", label: "Letter" },
  { value: "erratum", label: "Erratum" },
  { value: "paratext", label: "Paratext" },
]

export const SORT_OPTIONS = [
  { value: "relevance_score:desc", label: "Relevance" },
  { value: "cited_by_count:desc", label: "Most Cited" },
]

export const DEFAULT_FILTERS = {
  year_from: "",
  year_to: "",
  document_type: "",
  open_access_only: false,
}

export const DEFAULT_SORT = "relevance_score:desc"

export default function FilterPanel({ filters, sort, onFiltersChange, onSortChange }) {
  const [open, setOpen] = useState(false)

  const hasActiveFilters =
    filters.year_from ||
    filters.year_to ||
    filters.document_type ||
    filters.open_access_only ||
    sort !== DEFAULT_SORT

  const clearAll = () => {
    onFiltersChange({ ...DEFAULT_FILTERS })
    onSortChange(DEFAULT_SORT)
  }

  const handleFilterChange = (field, value) => {
    onFiltersChange({ ...filters, [field]: value })
  }

  return (
    <div className="w-full max-w-xl">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <SlidersHorizontal className="h-4 w-4" />
        Filters & Sort
        {hasActiveFilters && (
          <span className="h-1.5 w-1.5 rounded-full bg-blue-600" aria-label="Active filters" />
        )}
      </button>

      {open && (
        <div className="mt-3 rounded-lg border bg-card p-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="year_from" className="text-sm font-medium">
                Year from
              </label>
              <input
                id="year_from"
                type="number"
                placeholder="e.g. 2020"
                min="1900"
                max="2030"
                value={filters.year_from}
                onChange={(e) => handleFilterChange("year_from", e.target.value)}
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="year_to" className="text-sm font-medium">
                Year to
              </label>
              <input
                id="year_to"
                type="number"
                placeholder="e.g. 2026"
                min="1900"
                max="2030"
                value={filters.year_to}
                onChange={(e) => handleFilterChange("year_to", e.target.value)}
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="document_type" className="text-sm font-medium">
                Document type
              </label>
              <select
                id="document_type"
                value={filters.document_type}
                onChange={(e) => handleFilterChange("document_type", e.target.value)}
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm focus:border-blue-500 focus:outline-none"
              >
                {DOCUMENT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="sort_by" className="text-sm font-medium">
                Sort by
              </label>
              <select
                id="sort_by"
                value={sort}
                onChange={(e) => onSortChange(e.target.value)}
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm focus:border-blue-500 focus:outline-none"
              >
                {SORT_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <label className="mt-4 flex cursor-pointer items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={filters.open_access_only}
              onChange={(e) => handleFilterChange("open_access_only", e.target.checked)}
              className="h-4 w-4 rounded border-input accent-blue-600"
            />
            Open Access only
          </label>

          {hasActiveFilters && (
            <div className="mt-4 flex items-center justify-between border-t pt-3">
              <button
                type="button"
                onClick={clearAll}
                className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
              >
                <X className="h-3.5 w-3.5" />
                Clear all
              </button>
              <span className="text-xs text-muted-foreground">Applied when you search</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}