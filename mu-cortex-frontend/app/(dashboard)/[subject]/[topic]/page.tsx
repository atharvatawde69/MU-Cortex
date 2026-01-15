export default async function TopicVideosPage({
  params,
}: {
  params: Promise<{ subject: string; topic: string }>
}) {
  const { subject, topic } = await params

  return (
    <div className="space-y-2">
      <h1 className="text-2xl font-semibold">Topic: {topic}</h1>
      <p className="text-muted-foreground">
        Placeholder page for videos under <span className="font-medium">{subject}</span>{" "}
        / <span className="font-medium">{topic}</span>.
      </p>
    </div>
  )
}

