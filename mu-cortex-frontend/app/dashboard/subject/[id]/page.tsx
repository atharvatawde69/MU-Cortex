export default async function SubjectTopicsPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params

  // Validate that this is a UUID (strict check)
  const isUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)

  if (!isUUID) {
    return (
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold">Invalid Subject</h1>
        <p className="text-muted-foreground">
          The subject ID is invalid. Please return to the dashboard.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <h1 className="text-2xl font-semibold">Subject Topics</h1>
      <p className="text-muted-foreground">
        Placeholder page. This will list topics/modules for subject ID: {id}
      </p>
    </div>
  )
}
