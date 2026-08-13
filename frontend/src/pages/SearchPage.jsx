import { useState } from "react"
import { useForm } from "react-hook-form"
import { useNavigate } from "react-router-dom"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Loader2, Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import api, { getErrorMessage } from "@/lib/api"
import SearchHistory from "@/components/SearchHistory"
import FilterPanel, { DEFAULT_FILTERS, DEFAULT_SORT } from "@/components/FilterPanel"

export default function SearchPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { register, handleSubmit } = useForm()

  const [filters, setFilters] = useState({ ...DEFAULT_FILTERS })
  const [sort, setSort] = useState(DEFAULT_SORT)

  const searchMutation = useMutation({
    mutationFn: ({ query, filters, sort }) => {
      // Kirim hanya field yang punya nilai → null untuk yang kosong
      const body = {
        query,
        filters: {
          year_from: filters.year_from ? Number(filters.year_from) : null,
          year_to: filters.year_to ? Number(filters.year_to) : null,
          document_type: filters.document_type || null,
          open_access_only: filters.open_access_only,
        },
        sort_by: sort,
      }
      return api.post("/search", body).then((r) => r.data)
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["searches"] })
      // Simpan search params di sessionStorage agar "Load More" di ResultsPage tahu filter yang dipakai
      try {
        sessionStorage.setItem(
          `search-${data.search_id}`,
          JSON.stringify({ query: variables.query, filters: variables.filters, sort: variables.sort })
        )
      } catch {}
      navigate(`/results/${data.search_id}`, { state: { data } })
    },
    onError: (err) => toast.error(getErrorMessage(err, "Search failed. Please try again.")),
  })

  const onSubmit = (values) => {
    const query = values.query?.trim()
    if (!query) return

    // Validasi tahun sederhana
    if (filters.year_from && filters.year_to) {
      const from = Number(filters.year_from)
      const to = Number(filters.year_to)
      if (from > to) {
        toast.error("Year 'from' must be before or equal to year 'to'")
        return
      }
    }

    searchMutation.mutate({ query, filters, sort })
  }

  return (
    <div className="flex flex-col gap-12">
      <section className="flex flex-col items-center gap-4 pt-6 text-center sm:pt-14">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          What are you researching today?
        </h1>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="flex w-full max-w-xl flex-col gap-2 sm:flex-row"
        >
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="h-11 pl-9"
              placeholder="Search for papers... e.g.: the impact of long COVID on the heart"
              {...register("query", { required: true })}
            />
          </div>
          <Button type="submit" className="h-11 px-6" disabled={searchMutation.isPending}>
            {searchMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            Search
          </Button>
        </form>

        <FilterPanel
          filters={filters}
          sort={sort}
          onFiltersChange={setFilters}
          onSortChange={setSort}
        />

        <p className="text-xs text-muted-foreground">
          Ask in natural language — AI will find and summarize relevant papers for you.
        </p>
      </section>

      <SearchHistory onSelect={(id) => navigate(`/results/${id}`)} />
    </div>
  )
}