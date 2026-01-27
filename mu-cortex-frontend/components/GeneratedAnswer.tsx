"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

type GeneratedAnswerProps = {
  question_text: string
  marks: number
  answer: string
  generated_at: string
}

export default function GeneratedAnswer({
  question_text,
  marks,
  answer,
  generated_at,
}: GeneratedAnswerProps) {
  const [copied, setCopied] = useState(false)

  // Format answer text:
  // 1. Convert **bold** to <strong>
  // 2. Convert [DIAGRAM: ...] to highlighted block
  // 3. Preserve line breaks
  const formatAnswer = (text: string): string => {
    let formatted = text

    // Escape HTML first to prevent XSS
    formatted = formatted
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")

    // Convert [DIAGRAM: ...] to highlighted block
    formatted = formatted.replace(
      /\[DIAGRAM:\s*([^\]]+)\]/gi,
      '<div class="my-4 rounded-lg border-2 border-primary/20 bg-primary/5 p-4"><p class="text-sm font-semibold text-primary mb-2">📊 Diagram Required:</p><p class="text-sm text-muted-foreground">$1</p></div>'
    )

    // Convert **bold** to <strong>
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")

    // Convert line breaks to <br>
    formatted = formatted.replace(/\n/g, "<br />")

    return formatted
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(answer)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error("Failed to copy:", err)
    }
  }

  const formattedAnswer = formatAnswer(answer)
  const formattedDate = new Date(generated_at).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })

  return (
    <Card className="mt-4 border-l-4 border-l-primary">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-2">
            <CardTitle className="text-lg font-semibold">Generated Answer</CardTitle>
            <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <Badge variant="default">{marks}M</Badge>
              <span>•</span>
              <span>Generated {formattedDate}</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Formatted Answer */}
        <div
          className="prose prose-sm max-w-none text-foreground [&_strong]:font-semibold [&_strong]:text-foreground"
          dangerouslySetInnerHTML={{ __html: formattedAnswer }}
        />

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-2 pt-4 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={handleCopy}
            className="w-full sm:w-auto"
          >
            {copied ? "Copied!" : "Copy to Clipboard"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled
            className="w-full sm:w-auto"
          >
            Download as PDF (Coming Soon)
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
