export default async function SubjectTopicsPage({
  params,
}: {
  params: Promise<{ subject: string }>
}) {
  const { subject } = await params

  return (
    <div className="space-y-2">
      <h1 className="text-2xl font-semibold">Subject: {subject}</h1>
      <p className="text-muted-foreground">
        Placeholder page. This will list topics/modules for the subject.
      </p>
    </div>
  )
}

