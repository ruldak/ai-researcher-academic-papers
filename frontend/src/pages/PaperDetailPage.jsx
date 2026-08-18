import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { ArrowLeft, BarChart3, ExternalLink, FileDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import api from "@/lib/api"
import TypeBadge from "@/components/TypeBadge"
import OABadge from "@/components/OABadge"
import StatusButtons from "@/components/StatusButtons"
import TopicTag from "@/components/TopicTag"
import KeywordTag from "@/components/KeywordTag"
import NotesEditor from "@/components/NotesEditor"

export default function PaperDetailPage() {
  const { paperId } = useParams()
  const navigate = useNavigate()

  const { data, isLoading, isError } = useQuery({
    queryKey: ["paper", paperId],
    queryFn: () => api.get(`/papers/${paperId}`).then((r) => r.data),
  })

  const [status, setStatus] = useState("unread")
  useEffect(() => {
    if (data) setStatus(data.user_status?.status ?? "unread")
  }, [data])

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-9 w-36" />
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="mt-4 h-9 w-full max-w-md" />
        <Skeleton className="h-40 w-full rounded-lg" />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <p className="text-sm text-muted-foreground">Paper not found or failed to load.</p>
        <Button variant="outline" onClick={() => navigate(-1)}>
          <ArrowLeft /> Back
        </Button>
      </div>
    )
  }

  const { paper, user_status } = data
  const pdfUrl = paper.pdf_url || paper.oa_url
  const authorsText = paper.authors?.length
    ? paper.authors
        .map((a) => (a.institution ? `${a.name} (${a.institution})` : a.name))
        .join(", ")
    : "Unknown authors"

  return (
    <div className="flex flex-col gap-6">
      <Button
        variant="ghost"
        size="sm"
        className="-ml-2 w-fit text-muted-foreground"
        onClick={() => navigate(-1)}
      >
        <ArrowLeft className="h-4 w-4" /> Back to Results
      </Button>

      <header className="flex flex-col gap-3">
        <h1 className="text-xl font-semibold leading-snug sm:text-2xl">{paper.title}</h1>
        <p className="text-sm text-muted-foreground">{authorsText}</p>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-muted-foreground">
          <span>{paper.publication_year}</span>
          <TypeBadge type={paper.type} />
          {paper.is_oa && <OABadge />}
          <span className="inline-flex items-center gap-1">
            <BarChart3 className="h-3.5 w-3.5" /> {paper.cited_by_count ?? 0} cited
          </span>
          {paper.source_name && <span>{paper.source_name}</span>}
          {paper.doi && (
            <a
              href={paper.doi}
              target="_blank"
              rel="noreferrer"
              className="text-blue-600 hover:underline"
            >
              DOI
            </a>
          )}
        </div>
      </header>

      <Separator />

      <section>
        <h2 className="mb-2 text-sm font-semibold">Review status</h2>
        <StatusButtons paperId={paper.id} value={status} onChange={setStatus} />
      </section>

      <section>
        <h2 className="mb-2 text-sm font-semibold">Abstract</h2>
        <p className="whitespace-pre-line text-sm leading-relaxed text-foreground/90">
          {paper.abstract || "No abstract available"}
        </p>
      </section>

      {(paper.topics?.length > 0 || paper.keywords?.length > 0) && (
        <section className="flex flex-col gap-4">
          {paper.topics?.length > 0 && (
            <div>
              <h2 className="mb-2 text-sm font-semibold">Topics</h2>
              <div className="flex flex-wrap gap-1.5">
                {paper.topics.map((t) => (
                  <TopicTag key={t.name} name={t.name} />
                ))}
              </div>
            </div>
          )}
          {paper.keywords?.length > 0 && (
            <div>
              <h2 className="mb-2 text-sm font-semibold">Keywords</h2>
              <div className="flex flex-wrap gap-1.5">
                {paper.keywords.map((k) => (
                  <KeywordTag key={k.name} name={k.name} />
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      <section className="flex flex-wrap gap-2">
        {paper.landing_page_url && (
          <Button variant="outline" size="sm" asChild>
            <a href={paper.landing_page_url} target="_blank" rel="noreferrer">
              <ExternalLink className="h-4 w-4" /> View Original
            </a>
          </Button>
        )}
        {pdfUrl && (
          <Button variant="outline" size="sm" asChild>
            <a href={pdfUrl} target="_blank" rel="noreferrer">
              <FileDown className="h-4 w-4" /> Download PDF
            </a>
          </Button>
        )}
      </section>

      <Separator />

      <section>
        <h2 className="mb-2 text-sm font-semibold">My Notes</h2>
        <NotesEditor paperId={paper.id} initialNote={user_status?.note} />
      </section>
    </div>
  )
}