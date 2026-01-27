"use client"

import { useEffect, useState } from "react"
import { supabase } from "@/lib/supabase"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

type CommunityNote = {
  id: string
  file_name: string
  file_size: number | null
  tags: string[] | string | null
  telegram_message_link: string
  subject_id: string
  moderated_at: string | null
  moderated_by: string | null
}

type NotesListProps = {
  subjectId: string
}

function formatFileSize(bytes: number | null): string {
  if (!bytes) return "Unknown size"
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return "Awaiting moderation"
  
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (diffInSeconds < 60) return "Just now"
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} min ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hour${Math.floor(diffInSeconds / 3600) !== 1 ? "s" : ""} ago`
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} day${Math.floor(diffInSeconds / 86400) !== 1 ? "s" : ""} ago`
  
  // Fallback to formatted date
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

function parseTags(tags: string[] | string | null): string[] {
  if (!tags) return []
  if (Array.isArray(tags)) return tags
  // If it's a string, try to parse it (could be JSON or comma-separated)
  try {
    const parsed = JSON.parse(tags)
    return Array.isArray(parsed) ? parsed : [tags]
  } catch {
    // If not JSON, treat as comma-separated
    return tags.split(",").map((t) => t.trim()).filter(Boolean)
  }
}

export default function NotesList({ subjectId }: NotesListProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notes, setNotes] = useState<CommunityNote[]>([])

  useEffect(() => {
    const fetchNotes = async () => {
      try {
        setLoading(true)
        setError(null)

        const { data, error: supabaseError } = await supabase
          .from("community_resources")
          .select("id, file_name, file_size, tags, telegram_message_link, subject_id, moderated_at, moderated_by")
          .eq("subject_id", subjectId)

        if (supabaseError) {
          throw new Error(supabaseError.message)
        }

        // Sort: moderated_at DESC (approved first), then NULLS LAST (unmoderated at bottom)
        const sortedData = (data || []).sort((a, b) => {
          // If both have moderated_at, sort by date descending
          if (a.moderated_at && b.moderated_at) {
            return new Date(b.moderated_at).getTime() - new Date(a.moderated_at).getTime()
          }
          // If only a has moderated_at, a comes first
          if (a.moderated_at && !b.moderated_at) {
            return -1
          }
          // If only b has moderated_at, b comes first
          if (!a.moderated_at && b.moderated_at) {
            return 1
          }
          // Both are NULL, maintain original order
          return 0
        })

        setNotes(sortedData)
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Unable to load notes"
        console.error("Error fetching notes:", err)
        setError(errorMessage)
      } finally {
        setLoading(false)
      }
    }

    if (subjectId) {
      fetchNotes()
    }
  }, [subjectId])

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader>
              <div className="h-6 w-64 rounded-md bg-muted" />
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="h-4 w-32 rounded-md bg-muted" />
                <div className="flex gap-2">
                  <div className="h-6 w-16 rounded-full bg-muted" />
                  <div className="h-6 w-16 rounded-full bg-muted" />
                </div>
                <div className="h-9 w-32 rounded-md bg-muted" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-8 text-center">
        <div className="mx-auto max-w-sm space-y-3">
          <p className="text-lg font-medium text-foreground">
            Failed to load notes
          </p>
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
      </div>
    )
  }

  if (notes.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-12 text-center">
        <div className="mx-auto max-w-sm space-y-3">
          <p className="text-lg font-medium text-foreground">
            No community notes uploaded for this subject yet.
          </p>
          <p className="text-sm text-muted-foreground">
            Community notes will appear here once they are uploaded via Telegram.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {notes.map((note) => {
        const tags = parseTags(note.tags)
        return (
          <Card key={note.id} className="transition-shadow hover:shadow-md">
            <CardHeader>
              <CardTitle className="text-lg font-semibold">
                {note.file_name}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                <span>{formatFileSize(note.file_size)}</span>
                <span>•</span>
                {note.moderated_at ? (
                  <span>{formatRelativeTime(note.moderated_at)}</span>
                ) : (
                  <Badge variant="outline">Pending moderation</Badge>
                )}
              </div>

              {tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag, index) => (
                    <Badge key={index} variant="secondary">
                      #{tag}
                    </Badge>
                  ))}
                </div>
              )}

              <Button
                variant="default"
                onClick={() => {
                  window.open(note.telegram_message_link, "_blank", "noopener,noreferrer")
                }}
                className="w-full sm:w-auto"
              >
                Open in Telegram
              </Button>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
