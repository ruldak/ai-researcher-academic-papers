export default function KeywordTag({ name }) {
  return (
    <span className="rounded-full border border-amber-200 bg-amber-50 px-2.5 py-0.5 text-xs text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-300">
      {name}
    </span>
  )
}