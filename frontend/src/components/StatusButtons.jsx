import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import api, { getErrorMessage } from "@/lib/api"
import { STATUSES, STATUS_ACTIVE_CLASSES } from "@/lib/constants"
import { cn } from "@/lib/utils"

export default function StatusButtons({ paperId, value, onChange }) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (status) =>
      api.patch(`/papers/${paperId}/status`, { status }).then((r) => r.data),
    onSuccess: (res) => {
      onChange(res.status)
      queryClient.invalidateQueries({ queryKey: ["paper", paperId] })
      toast.success(`Marked as ${res.status}`)
    },
    onError: (err) => toast.error(getErrorMessage(err, "Failed to update status")),
  })

  return (
    <div className="flex flex-wrap gap-2">
      {STATUSES.map(({ value: v, label, icon: Icon }) => {
        const active = v === value
        return (
          <Button
            key={v}
            type="button"
            size="sm"
            variant="outline"
            disabled={mutation.isPending}
            onClick={() => !active && mutation.mutate(v)}
            className={cn(active && STATUS_ACTIVE_CLASSES[v])}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Button>
        )
      })}
    </div>
  )
}