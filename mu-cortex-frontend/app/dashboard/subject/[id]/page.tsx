"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import QuestionsList from "@/components/QuestionsList"

type SchemeSelection = {
  scheme: string
  branch: string
  semester: number
}

type Topic = {
  id: string
  name: string
}

type Module = {
  module_number: number
  topics: Topic[]
}

type TopicsResponse = {
  subject_id: string
  subject_name: string
  total_topics: number
  modules: Module[]
}

export default function SubjectTopicsPage() {
  const params = useParams()
  const router = useRouter()
  const subject_id = params.id as string

  const [activeTab, setActiveTab] = useState<'topics' | 'questions'>('topics')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<TopicsResponse | null>(null)

  useEffect(() => {
    const fetchTopics = async () => {
      try {
        setLoading(true)
        setError(null)

        // Read scheme selection from localStorage
        const stored = window.localStorage.getItem("mu_cortex_scheme")
        if (!stored) {
          setError("No scheme selected. Please select a scheme first.")
          setLoading(false)
          return
        }

        const selection: SchemeSelection = JSON.parse(stored)
        const { scheme } = selection

        // Call backend endpoint
        const response = await fetch(
          `http://127.0.0.1:8000/topics?subject_id=${subject_id}&scheme_id=${scheme}`
        )

        if (!response.ok) {
          const errorText = await response.text()
          console.error("API Error:", {
            status: response.status,
            statusText: response.statusText,
            body: errorText,
          })
          throw new Error(
            `Failed to fetch topics: ${response.status} ${response.statusText}`
          )
        }

        const topicsData: TopicsResponse = await response.json()
        setData(topicsData)
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Unable to load topics"
        console.error("Error fetching topics:", err)
        setError(errorMessage)
      } finally {
        setLoading(false)
      }
    }

    if (subject_id) {
      fetchTopics()
    }
  }, [subject_id])

  if (loading && activeTab === "topics") {
    return (
      <div className="space-y-6">
        <div className="space-y-3">
          <div className="h-8 w-64 animate-pulse rounded-md bg-muted" />
          <div className="h-4 w-48 animate-pulse rounded-md bg-muted" />
        </div>

        {/* Tab Navigation */}
        <div className="border-b">
          <nav className="-mb-px flex gap-2">
            <button
              onClick={() => setActiveTab("topics")}
              className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "topics"
                  ? "border-b-2 border-primary bg-background text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              Topics
            </button>
            <button
              onClick={() => setActiveTab("questions")}
              className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "questions"
                  ? "border-b-2 border-primary bg-background text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              Questions
            </button>
          </nav>
        </div>

        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-6 w-40 rounded-md bg-muted" />
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {[1, 2, 3, 4].map((j) => (
                    <div
                      key={j}
                      className="h-11 w-full rounded-md bg-muted"
                      style={{
                        animationDelay: `${j * 100}ms`,
                      }}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (loading && activeTab === "questions") {
    return (
      <div className="space-y-6">
        <div className="space-y-3">
          <div className="h-8 w-64 animate-pulse rounded-md bg-muted" />
          <div className="h-4 w-48 animate-pulse rounded-md bg-muted" />
        </div>

        {/* Tab Navigation */}
        <div className="border-b">
          <nav className="-mb-px flex gap-2">
            <button
              onClick={() => setActiveTab("topics")}
              className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "topics"
                  ? "border-b-2 border-primary bg-background text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              Topics
            </button>
            <button
              onClick={() => setActiveTab("questions")}
              className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "questions"
                  ? "border-b-2 border-primary bg-background text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              Questions
            </button>
          </nav>
        </div>

        <QuestionsList subjectId={subject_id} />
      </div>
    )
  }

  if (error && activeTab === "topics") {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold">Error</h1>
        </div>

        {/* Tab Navigation */}
        <div className="border-b">
          <nav className="-mb-px flex gap-2">
            <button
              onClick={() => setActiveTab("topics")}
              className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "topics"
                  ? "border-b-2 border-primary bg-background text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              Topics
            </button>
            <button
              onClick={() => setActiveTab("questions")}
              className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "questions"
                  ? "border-b-2 border-primary bg-background text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              Questions
            </button>
          </nav>
        </div>

        <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-8 text-center">
          <div className="mx-auto max-w-sm space-y-3">
            <p className="text-lg font-medium text-foreground">
              Unable to load topics
            </p>
            <p className="text-sm text-muted-foreground">{error}</p>
            <div className="pt-4">
              <Button
                variant="outline"
                onClick={() => router.push("/dashboard")}
              >
                Back to Dashboard
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error && activeTab === "questions") {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold">Error</h1>
        </div>

        {/* Tab Navigation */}
        <div className="border-b">
          <nav className="-mb-px flex gap-2">
            <button
              onClick={() => setActiveTab("topics")}
              className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "topics"
                  ? "border-b-2 border-primary bg-background text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              Topics
            </button>
            <button
              onClick={() => setActiveTab("questions")}
              className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "questions"
                  ? "border-b-2 border-primary bg-background text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              Questions
            </button>
          </nav>
        </div>

        <QuestionsList subjectId={subject_id} />
      </div>
    )
  }

  if ((!data || data.modules.length === 0) && activeTab === "topics") {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold">
            {data?.subject_name || "Subject Topics"}
          </h1>
        </div>

        {/* Tab Navigation */}
        <div className="border-b">
          <nav className="-mb-px flex gap-2">
            <button
              onClick={() => setActiveTab("topics")}
              className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "topics"
                  ? "border-b-2 border-primary bg-background text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              Topics
            </button>
            <button
              onClick={() => setActiveTab("questions")}
              className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "questions"
                  ? "border-b-2 border-primary bg-background text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              Questions
            </button>
          </nav>
        </div>

        <div className="rounded-lg border border-dashed p-12 text-center">
          <div className="mx-auto max-w-sm space-y-3">
            <p className="text-lg font-medium text-foreground">
              No topics available
            </p>
            <p className="text-sm text-muted-foreground">
              This subject doesn't have any topics yet. Please check back later or contact support if this seems incorrect.
            </p>
            <div className="pt-4">
              <Button
                variant="outline"
                onClick={() => router.push("/dashboard")}
              >
                Back to Dashboard
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if ((!data || data.modules.length === 0) && activeTab === "questions") {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold">
            {data?.subject_name || "Subject"}
          </h1>
        </div>

        {/* Tab Navigation */}
        <div className="border-b">
          <nav className="-mb-px flex gap-2">
            <button
              onClick={() => setActiveTab("topics")}
              className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "topics"
                  ? "border-b-2 border-primary bg-background text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              Topics
            </button>
            <button
              onClick={() => setActiveTab("questions")}
              className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "questions"
                  ? "border-b-2 border-primary bg-background text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              Questions
            </button>
          </nav>
        </div>

        <QuestionsList subjectId={subject_id} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">{data.subject_name}</h1>
        <p className="text-sm text-muted-foreground">
          {data.total_topics} topic{data.total_topics !== 1 ? "s" : ""} across{" "}
          {data.modules.length} module{data.modules.length !== 1 ? "s" : ""}
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b">
        <nav className="-mb-px flex gap-2">
          <button
            onClick={() => setActiveTab("topics")}
            className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === "topics"
                ? "border-b-2 border-primary bg-background text-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-accent"
            }`}
          >
            Topics
          </button>
          <button
            onClick={() => setActiveTab("questions")}
            className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === "questions"
                ? "border-b-2 border-primary bg-background text-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-accent"
            }`}
          >
            Questions
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === "questions" ? (
        <QuestionsList subjectId={subject_id} />
      ) : (
        <div className="space-y-4">
        {data.modules.map((module) => (
          <Card key={module.module_number}>
            <CardHeader>
              <CardTitle className="text-xl font-semibold">
                Module {module.module_number}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {module.topics.length === 0 ? (
                  <div className="rounded-md border border-dashed p-6 text-center">
                    <p className="text-sm text-muted-foreground">
                      No topics in this module yet.
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                    {module.topics.map((topic) => (
                      <Button
                        key={topic.id}
                        variant="outline"
                        className="h-auto justify-between py-3 text-left font-normal"
                        asChild
                      >
                        <Link href={`/dashboard/subject/${subject_id}/${topic.id}`}>
                          <span className="truncate pr-2">{topic.name}</span>
                          <span className="shrink-0 text-xs text-muted-foreground">
                            →
                          </span>
                        </Link>
                      </Button>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
        </div>
      )}
    </div>
  )
}
