"use client"

import { useEffect, useState } from "react"
import { SubjectCard } from "@/components/SubjectCard"

type SchemeSelection = {
  scheme: string
  branch: string
  semester: number
}

type Subject = {
  id: string
  name: string
  code: string
  scheme_id: string
}

export default function DashboardHomePage() {
  const [loading, setLoading] = useState(true)
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const stored = window.localStorage.getItem("mu_cortex_scheme")
    if (!stored) {
      setError("No scheme selected")
      setLoading(false)
      return
    }

    try {
      const selection: SchemeSelection = JSON.parse(stored)
      const { scheme: scheme_id, branch, semester } = selection

      const fetchSubjects = async () => {
        try {
          setLoading(true)
          setError(null)
          const response = await fetch(
            `http://127.0.0.1:8000/subjects?scheme_id=${scheme_id}&branch=${branch}&semester=${semester}`
          )

          if (!response.ok) {
            throw new Error("Failed to fetch subjects")
          }

          const data = await response.json()
          setSubjects(data || [])
        } catch (err) {
          setError("Unable to load subjects. Try again later.")
        } finally {
          setLoading(false)
        }
      }

      fetchSubjects()
    } catch {
      setError("No scheme selected")
      setLoading(false)
    }
  }, [])

  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold">Your Subjects</h1>
      </div>

      {loading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <SubjectCard
              key={i}
              id=""
              name=""
              code=""
              scheme_id=""
              loading={true}
            />
          ))}
        </div>
      )}

      {!loading && error && (
        <p className="text-muted-foreground">{error}</p>
      )}

      {!loading && !error && subjects.length === 0 && (
        <p className="text-muted-foreground">
          No subjects available for your scheme.
        </p>
      )}

      {!loading && !error && subjects.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {subjects.map((subject) => (
            <SubjectCard
              key={subject.id}
              id={subject.id}
              name={subject.name}
              code={subject.code}
              scheme_id={subject.scheme_id}
              topicsCount={0}
            />
          ))}
        </div>
      )}
    </div>
  )
}
