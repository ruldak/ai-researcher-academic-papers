import { useEffect, useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { toast } from "sonner"
import { Loader2, Save } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import api, { getErrorMessage } from "@/lib/api"

const MAX_LENGTH = 10000

export default function NotesEditor({ paperId, initialNote }) {
  const [note, setNote] = useState(initialNote ?? "")
  const [savedNote, setSavedNote] = useState(initialNote ?? "")

  useEffect(() => {
    setNote(initialNote ?? "")
    setSavedNote(initialNote ?? "")
  }, [initialNote])

  const mutation = useMutation({
    mutationFn: (value) =>
      api.patch(`/papers/${paperId}/note`, { note: value || null }).then((r) => r.data),
    onSuccess: () => {
      setSavedNote(note)
      toast.success("Note saved")
    },
    onError: (err) => toast.error(getErrorMessage(err, "Failed to save note")),
  })

  const dirty = note !== savedNote

  return (
    <div className="flex flex-col gap-2">
      <Textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        maxLength={MAX_LENGTH}
        rows={5}
        placeholder="Write notes for this paper..."
      />
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">
          {note.length}/{MAX_LENGTH}
        </span>
        <Button size="sm" onClick={() => mutation.mutate(note)} disabled={!dirty || mutation.isPending}>
          {mutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          Save Note
        </Button>
      </div>
    </div>
  )
}