import { useState } from "react"
import { useLocation, useNavigate, useParams } from "react-router-dom"
import { useMutation, useQuery } from "@tanstack/react-query"
import { toast } from "sonner"
import { ArrowLeft, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import api, { getErrorMessage } from "@/lib/api"
import AISummaryBox from "@/components/AISummaryBox"
import PaperCard from "@/components/PaperCard"

export default function ResultsPage() {
  const { searchId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const passedData = location.state?.data ?? null

  const [extraPapers, setExtraPapers] = useState([])
  const [nextPage, setNextPage] = useState(2)

  const { data, isLoading, isError } = useQuery({
    queryKey: ["search", searchId],
    queryFn: () => api.get(`/searches/${searchId}`).then((r) => r.data),
    initialData: passedData ?? undefined,
  })

  const loadMore = useMutation({
    mutationFn: (page) => {
      // Ambil filter & sort dari sessionStorage (disimpan saat search pertama)
      let filters = null
      let sort = "relevance_score:desc"
      try {
        const saved = sessionStorage.getItem(`search-${searchId}`)
        if (saved) {
          const parsed = JSON.parse(saved)
          filters = parsed.filters
          sort = parsed.sort
        }
      } catch {}

      const body = {
        query: data.query_text,
        page,
        filters: filters
          ? {
              year_from: filters.year_from ? Number(filters.year_from) : null,
              year_to: filters.year_to ? Number(filters.year_to) : null,
              document_type: filters.document_type || null,
              open_access_only: !!filters.open_access_only,
            }
          : undefined,
        sort_by: sort,
      }

      return api.post("/search", body).then((r) => r.data)
    },
    onSuccess: (res) => {
      setExtraPapers((prev) => [...prev, ...(res.papers ?? [])])
      setNextPage((p) => p + 1)
    },
    onError: (err) => toast.error(getErrorMessage(err, "Could not load more results")),
  })

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-9 w-36" />
        <Skeleton className="h-28 w-full rounded-lg" />
        <Skeleton className="h-5 w-64" />
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-28 w-full rounded-lg" />
        ))}
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <p className="text-sm text-muted-foreground">This search could not be loaded.</p>
        <Button variant="outline" onClick={() => navigate("/")}>
          <ArrowLeft /> Back to Search
        </Button>
      </div>
    )
  }

  const papers = [...(data.papers ?? []), ...extraPapers]
  const hasMore = papers.length < data.total_count

  return (
    <div className="flex flex-col gap-4">
      <Button
        variant="ghost"
        size="sm"
        className="-ml-2 w-fit text-muted-foreground"
        onClick={() => navigate("/")}
      >
        <ArrowLeft className="h-4 w-4" /> Back to Search
      </Button>

      <AISummaryBox summary={data.ai_summary} />

      <p className="text-sm text-muted-foreground">
        Found <span className="font-medium text-foreground">{data.total_count}</span>{" "}
        {data.total_count === 1 ? "paper" : "papers"} for query{" "}
        <span className="font-medium text-foreground">"{data.query_text}"</span>
      </p>

      {papers.length > 0 ? (
        <div className="flex flex-col gap-3">
          {papers.map((paper) => (
            <PaperCard key={paper.id} paper={paper} />
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed p-10 text-center text-sm text-muted-foreground">
          No papers found. Try a different query or adjust filters.
        </div>
      )}

      {hasMore && (
        <Button
          variant="outline"
          className="mx-auto mt-2"
          onClick={() => loadMore.mutate(nextPage)}
          disabled={loadMore.isPending}
        >
          {loadMore.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
          Load more results
        </Button>
      )}
    </div>
  )
}