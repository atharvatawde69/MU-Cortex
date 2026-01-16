"use client"

import { useEffect, useState, FormEvent } from "react"
import { useParams } from "next/navigation"
import Image from "next/image"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

type SchemeSelection = {
  scheme: string
  branch: string
  semester: number
}

type Video = {
  title: string
  channel: string
  youtube_url: string
  engagement_score: number
  views: number
  comments: number
}

type VideosResponse = {
  topic_id?: string
  topic_name?: string
  videos: Video[]
  cached?: boolean
  count?: number
  [key: string]: unknown // Allow other fields from backend
}

// Extract YouTube video ID from URL
function extractVideoId(youtubeUrl: string): string {
  // Handle various YouTube URL formats
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
    /youtube\.com\/watch\?.*v=([^&\n?#]+)/,
  ]

  for (const pattern of patterns) {
    const match = youtubeUrl.match(pattern)
    if (match && match[1]) {
      return match[1]
    }
  }

  // Fallback: try to extract from URL directly
  const urlParts = youtubeUrl.split("v=")
  if (urlParts.length > 1) {
    return urlParts[1].split("&")[0].split("#")[0]
  }

  return ""
}

// Generate YouTube thumbnail URL
function getThumbnailUrl(youtubeUrl: string): string {
  const videoId = extractVideoId(youtubeUrl)
  if (!videoId) {
    return "/placeholder-thumbnail.jpg" // Fallback
  }
  return `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`
}

export default function TopicVideosPage() {
  const params = useParams()
  const topic_id = params.topic as string
  const subject_id = params.id as string

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<VideosResponse | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [defaultTopicName, setDefaultTopicName] = useState<string | null>(null)

  // Fetch default topic name on mount
  useEffect(() => {
    const fetchTopicName = async () => {
      try {
        const stored = window.localStorage.getItem("mu_cortex_scheme")
        if (!stored) return

        const selection: SchemeSelection = JSON.parse(stored)
        const { scheme } = selection

        const topicsResponse = await fetch(
          `http://127.0.0.1:8000/topics?subject_id=${subject_id}&scheme_id=${scheme}`
        )
        if (topicsResponse.ok) {
          const topicsData = await topicsResponse.json()
          // Find the topic name by searching through all modules
          for (const module of topicsData.modules || []) {
            const topic = module.topics?.find((t: { id: string }) => t.id === topic_id)
            if (topic) {
              setDefaultTopicName(topic.name)
              break
            }
          }
        }
      } catch (err) {
        console.warn("Failed to fetch topic name:", err)
      }
    }

    if (topic_id && subject_id) {
      fetchTopicName()
    }
  }, [topic_id, subject_id])

  // Fetch videos function
  const fetchVideos = async (queryOverride?: string | null) => {
    try {
      setLoading(true)
      setError(null)
      setData(null) // Reset videos state on new search

      // Read scheme selection from localStorage
      const stored = window.localStorage.getItem("mu_cortex_scheme")
      if (!stored) {
        setError("No scheme selected. Please select a scheme first.")
        setLoading(false)
        return
      }

      const selection: SchemeSelection = JSON.parse(stored)
      const { scheme } = selection

      // Determine query: use override if provided, else use default topic name, else empty
      const query = queryOverride !== undefined 
        ? (queryOverride || defaultTopicName || null)
        : (defaultTopicName || null)

      // Build API URL
      let apiUrl = `http://127.0.0.1:8000/videos?topic_id=${topic_id}&scheme_id=${scheme}`
      if (query) {
        apiUrl += `&query=${encodeURIComponent(query)}`
      }

      // Call backend endpoint
      const response = await fetch(apiUrl)

      if (!response.ok) {
        const errorText = await response.text()
        console.error("API Error:", {
          status: response.status,
          statusText: response.statusText,
          body: errorText,
        })
        throw new Error(
          `Failed to fetch videos: ${response.status} ${response.statusText}`
        )
      }

      const videosData: VideosResponse = await response.json()
      setData(videosData)
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Unable to load videos"
      console.error("Error fetching videos:", err)
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  // Initial fetch on mount
  useEffect(() => {
    if (topic_id) {
      fetchVideos(undefined)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topic_id])

  // Handle search form submission
  const handleSearch = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const trimmedQuery = searchQuery.trim()
    // If input is empty, use default topic name (pass null to use default)
    // If input has value, use that as query
    fetchVideos(trimmedQuery || null)
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="h-8 w-64 animate-pulse rounded-md bg-muted" />
            <div className="h-6 w-16 animate-pulse rounded-full bg-muted" />
          </div>
          <div className="h-4 w-48 animate-pulse rounded-md bg-muted" />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card
              key={i}
              className="animate-pulse overflow-hidden"
              style={{
                animationDelay: `${i * 100}ms`,
              }}
            >
              <div className="relative aspect-video w-full bg-muted" />
              <CardHeader className="gap-2">
                <div className="h-5 w-full rounded-md bg-muted" />
                <div className="h-4 w-2/3 rounded-md bg-muted" />
              </CardHeader>
              <CardContent>
                <div className="h-4 w-1/2 rounded-md bg-muted" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold">Error</h1>
        </div>
        <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-8 text-center">
          <div className="mx-auto max-w-sm space-y-3">
            <p className="text-lg font-medium text-foreground">
              Failed to load videos
            </p>
            <p className="text-sm text-muted-foreground">
              We couldn't fetch the videos for this topic. Please try again later or check your connection.
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (!data || !data.videos || data.videos.length === 0) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold">
            {data?.topic_name || "Topic Videos"}
          </h1>
        </div>
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search within this topic (e.g. Banker's Algorithm example)"
            className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          />
          <Button type="submit" disabled={loading}>
            Search
          </Button>
        </form>
        <div className="rounded-lg border border-dashed p-12 text-center">
          <div className="mx-auto max-w-sm space-y-3">
            <p className="text-lg font-medium text-foreground">
              No videos found
            </p>
            <p className="text-sm text-muted-foreground">
              We couldn't find any videos for this topic. The content may still be being processed, or there may not be any videos available yet.
            </p>
          </div>
        </div>
      </div>
    )
  }

  const topicName = data.topic_name || "Topic Videos"
  const isCached = data.cached === true
  const videoCount = data.count ?? (data as { videos_found?: number }).videos_found ?? data.videos.length

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-3xl font-bold">{topicName}</h1>
          {isCached && (
            <Badge variant="secondary">Cached</Badge>
          )}
        </div>
        <p className="text-sm text-muted-foreground">
          {videoCount} video{videoCount !== 1 ? "s" : ""} available
        </p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search within this topic (e.g. Banker's Algorithm example)"
          className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        />
        <Button type="submit" disabled={loading}>
          Search
        </Button>
      </form>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data.videos.map((video, index) => {
          const thumbnailUrl = getThumbnailUrl(video.youtube_url)

          return (
            <Card
              key={index}
              className="cursor-pointer overflow-hidden transition-shadow hover:shadow-md"
              onClick={() => {
                window.open(video.youtube_url, "_blank", "noopener,noreferrer")
              }}
            >
              <div className="relative aspect-video w-full bg-muted">
                <Image
                  src={thumbnailUrl}
                  alt={video.title}
                  fill
                  className="object-cover"
                  sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw"
                  onError={(e) => {
                    // Fallback to hqdefault if maxresdefault fails
                    const videoId = extractVideoId(video.youtube_url)
                    if (videoId) {
                      const target = e.target as HTMLImageElement
                      target.src = `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`
                    }
                  }}
                />
              </div>
              <CardHeader className="gap-1">
                <CardTitle className="line-clamp-2 text-base font-semibold">
                  {video.title}
                </CardTitle>
                <p className="text-sm text-muted-foreground">{video.channel}</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-1 text-sm">
                  <div className="text-muted-foreground">
                    Popularity:{" "}
                    <span className="font-medium text-foreground">
                      {video.engagement_score.toLocaleString()}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
