import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"

export function SubjectCard({
  id,
  name,
  code,
  scheme_id,
  topicsCount = 0,
  loading = false,
}: {
  id: string
  name: string
  code: string
  scheme_id: string
  topicsCount?: number
  loading?: boolean
}) {
  if (loading) {
    return (
      <Card className="animate-pulse">
        <CardHeader>
          <div className="space-y-2">
            <div className="h-5 w-3/4 rounded bg-muted" />
            <div className="h-4 w-1/2 rounded bg-muted" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-4 w-2/3 rounded bg-muted" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Link href={`/dashboard/subject/${id}`} className="block">
      <Card className="cursor-pointer transition-shadow hover:shadow-sm">
        <CardHeader>
          <div className="flex items-start justify-between gap-3">
            <CardTitle className="leading-snug">{name}</CardTitle>
            <Badge variant="secondary">{scheme_id}</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">{code}</div>
            <div className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">{topicsCount}</span> Topics
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}

