"use client"

import { useEffect, useState, useMemo } from "react"
import { supabase } from "@/lib/supabase"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import GeneratedAnswer from "@/components/GeneratedAnswer"

type Question = {
  id: string
  question_text: string
  marks: number
  topic_id: string
}

type QuestionsListProps = {
  subjectId: string
  // topicId kept for easy rollback but not used for filtering
  topicId?: string
}

type MarksFilter = "all" | "2" | "5" | "10"
type SortOption = "frequency" | "marks"

type GeneratedAnswerData = {
  question_id: string
  answer: string
  generated_at: string
}

// Mock frequency_score for now (default to 1)
// TODO: Replace with real frequency_score from backend when available
function getFrequencyScore(question: Question): number {
  return 1 // Temporary: will be replaced with question.frequency_score
}

export default function QuestionsList({ subjectId, topicId }: QuestionsListProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [questions, setQuestions] = useState<Question[]>([])
  const [marksFilter, setMarksFilter] = useState<MarksFilter>("all")
  const [highFrequencyOnly, setHighFrequencyOnly] = useState(false)
  const [sortBy, setSortBy] = useState<SortOption>("frequency")
  
  // Answer generation state
  const [generatingQuestionId, setGeneratingQuestionId] = useState<string | null>(null)
  const [generatedAnswers, setGeneratedAnswers] = useState<Map<string, GeneratedAnswerData>>(new Map())
  const [generationErrors, setGenerationErrors] = useState<Map<string, string>>(new Map())
  const [expandedQuestionId, setExpandedQuestionId] = useState<string | null>(null)

  // Filter and sort questions - MUST run before any conditional returns
  const filteredAndSortedQuestions = useMemo(() => {
    let filtered = [...questions]

    // Apply marks filter
    if (marksFilter !== "all") {
      filtered = filtered.filter((q) => q.marks === parseInt(marksFilter))
    }

    // Apply high frequency filter
    if (highFrequencyOnly) {
      filtered = filtered.filter((q) => getFrequencyScore(q) >= 2)
    }

    // Apply sorting
    filtered.sort((a, b) => {
      if (sortBy === "frequency") {
        const freqA = getFrequencyScore(a)
        const freqB = getFrequencyScore(b)
        return freqB - freqA // Descending: higher frequency first
      } else {
        // Sort by marks (descending: 10M, 5M, 2M)
        return b.marks - a.marks
      }
    })

    return filtered
  }, [questions, marksFilter, highFrequencyOnly, sortBy])

  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch questions via question_appearances to filter by subject_id
        // Step 1: Get all question_ids for this subject from question_appearances
        const { data: appearances, error: appearancesError } = await supabase
          .from("question_appearances")
          .select("question_id")
          .eq("subject_id", subjectId)

        if (appearancesError) {
          throw new Error(appearancesError.message)
        }

        if (!appearances || appearances.length === 0) {
          setQuestions([])
          return
        }

        // Step 2: Get unique question IDs (deduplicate)
        const uniqueQuestionIds = [
          ...new Set(appearances.map((a) => a.question_id)),
        ]

        // Step 3: Fetch the actual questions
        const { data: questionsData, error: questionsError } = await supabase
          .from("questions")
          .select("id, question_text, marks, topic_id")
          .in("id", uniqueQuestionIds)

        if (questionsError) {
          throw new Error(questionsError.message)
        }

        setQuestions(questionsData || [])
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Unable to load questions"
        console.error("Error fetching questions:", err)
        setError(errorMessage)
      } finally {
        setLoading(false)
      }
    }

    if (subjectId) {
      fetchQuestions()
    }
  }, [subjectId])

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader>
              <div className="h-6 w-full rounded-md bg-muted" />
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex gap-2">
                  <div className="h-6 w-12 rounded-full bg-muted" />
                  <div className="h-6 w-24 rounded-full bg-muted" />
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
            Failed to load questions
          </p>
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
      </div>
    )
  }

  // Generate answer for a question
  const handleGenerateAnswer = async (questionId: string) => {
    try {
      setGeneratingQuestionId(questionId)
      setGenerationErrors((prev) => {
        const newMap = new Map(prev)
        newMap.delete(questionId)
        return newMap
      })

      // Collapse previous answer if any
      setExpandedQuestionId(questionId)

      const response = await fetch("http://127.0.0.1:8000/answers/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question_id: questionId }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(
          `Failed to generate answer: ${response.status} ${response.statusText}${errorText ? ` - ${errorText}` : ""}`
        )
      }

      const data: { question_id: string; answer: string } = await response.json()

      // Store generated answer
      setGeneratedAnswers((prev) => {
        const newMap = new Map(prev)
        newMap.set(questionId, {
          question_id: data.question_id,
          answer: data.answer,
          generated_at: new Date().toISOString(),
        })
        return newMap
      })
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Unable to generate answer"
      console.error("Error generating answer:", err)
      setGenerationErrors((prev) => {
        const newMap = new Map(prev)
        newMap.set(questionId, errorMessage)
        return newMap
      })
    } finally {
      setGeneratingQuestionId(null)
    }
  }

  if (questions.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-12 text-center">
        <div className="mx-auto max-w-sm space-y-3">
          <p className="text-lg font-medium text-foreground">
            No questions available for this subject yet.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filter and Sort Controls */}
      <div className="space-y-4 rounded-lg border bg-card p-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          {/* Marks Filter */}
          <div className="flex items-center gap-2">
            <label htmlFor="marks-filter" className="text-sm font-medium">
              Marks:
            </label>
            <select
              id="marks-filter"
              value={marksFilter}
              onChange={(e) => setMarksFilter(e.target.value as MarksFilter)}
              className="rounded-md border border-input bg-background px-3 py-1.5 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <option value="all">All</option>
              <option value="2">2 Marks</option>
              <option value="5">5 Marks</option>
              <option value="10">10 Marks</option>
            </select>
          </div>

          {/* High Frequency Toggle */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="high-frequency"
              checked={highFrequencyOnly}
              onChange={(e) => setHighFrequencyOnly(e.target.checked)}
              className="h-4 w-4 rounded border-input accent-primary"
            />
            <label htmlFor="high-frequency" className="text-sm font-medium cursor-pointer">
              High Frequency Only
            </label>
          </div>

          {/* Sort Control */}
          <div className="flex items-center gap-2">
            <label htmlFor="sort-by" className="text-sm font-medium">
              Sort by:
            </label>
            <select
              id="sort-by"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="rounded-md border border-input bg-background px-3 py-1.5 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <option value="frequency">Frequency</option>
              <option value="marks">Marks</option>
            </select>
          </div>
        </div>

        {/* Helper UI */}
        <div className="flex flex-wrap items-center gap-3 pt-2 border-t">
          <Badge variant="secondary">
            {filteredAndSortedQuestions.length} question{filteredAndSortedQuestions.length !== 1 ? "s" : ""} shown
          </Badge>
          <p className="text-xs text-muted-foreground">
            Frequency is estimated (beta)
          </p>
        </div>
      </div>

      {/* Questions List */}
      {filteredAndSortedQuestions.length === 0 ? (
        <div className="rounded-lg border border-dashed p-12 text-center">
          <div className="mx-auto max-w-sm space-y-3">
            <p className="text-lg font-medium text-foreground">
              No questions match your filters
            </p>
            <p className="text-sm text-muted-foreground">
              Try adjusting your filter settings to see more questions.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAndSortedQuestions.map((question) => {
            const frequencyScore = getFrequencyScore(question)
            const isGenerating = generatingQuestionId === question.id
            const generatedAnswer = generatedAnswers.get(question.id)
            const generationError = generationErrors.get(question.id)
            const isExpanded = expandedQuestionId === question.id

            return (
              <div key={question.id}>
                <Card className="transition-shadow hover:shadow-md">
                  <CardHeader>
                    <CardTitle className="text-base font-semibold leading-relaxed">
                      {question.question_text}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="default">
                        {question.marks}M
                      </Badge>
                      <Badge variant="secondary">
                        Frequency: {frequencyScore}×
                      </Badge>
                    </div>

                    <Button
                      variant="default"
                      onClick={() => handleGenerateAnswer(question.id)}
                      disabled={isGenerating}
                      className="w-full sm:w-auto"
                    >
                      {isGenerating ? (
                        <>
                          <span className="mr-2">Generating...</span>
                          <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                        </>
                      ) : generatedAnswer ? (
                        "Regenerate Answer"
                      ) : (
                        "Generate Answer"
                      )}
                    </Button>

                    {/* Generation Error */}
                    {generationError && (
                      <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-3">
                        <p className="text-sm text-destructive">{generationError}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Generated Answer */}
                {isExpanded && generatedAnswer && (
                  <GeneratedAnswer
                    question_text={question.question_text}
                    marks={question.marks}
                    answer={generatedAnswer.answer}
                    generated_at={generatedAnswer.generated_at}
                  />
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
