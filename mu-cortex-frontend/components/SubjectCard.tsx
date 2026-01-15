import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function SubjectCard({
  subjectName,
  moduleCount,
}: {
  subjectName: string
  moduleCount: number
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{subjectName}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground">
          Modules: <span className="font-medium text-foreground">{moduleCount}</span>
        </div>
      </CardContent>
    </Card>
  )
}

