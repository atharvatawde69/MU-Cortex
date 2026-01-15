import Image from "next/image"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function VideoCard({
  title,
  thumbnailUrl,
  engagementScore,
}: {
  title: string
  thumbnailUrl: string
  engagementScore: number
}) {
  return (
    <Card className="overflow-hidden">
      <div className="relative aspect-video w-full bg-muted">
        <Image
          src={thumbnailUrl}
          alt={title}
          fill
          className="object-cover"
          sizes="(max-width: 768px) 100vw, 33vw"
        />
      </div>
      <CardHeader className="gap-1">
        <CardTitle className="line-clamp-2 text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground">
          Engagement score:{" "}
          <span className="font-medium text-foreground">{engagementScore}</span>
        </div>
      </CardContent>
    </Card>
  )
}

