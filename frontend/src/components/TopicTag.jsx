export default function TopicTag({ name }) {
  return (
    <span className="rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-0.5 text-xs text-indigo-700 dark:border-indigo-900 dark:bg-indigo-950 dark:text-indigo-300">
      {name}
    </span>
  )
}