"use client"

import * as React from "react"
import { ChevronDown } from "lucide-react"
import { useRouter } from "next/navigation"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { supabase } from "@/lib/supabase"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

type Scheme = "2019" | "2024"

type SchemeSelection = {
  scheme: Scheme
  branch: string
  semester: number
}

const STORAGE_KEY = "mu_cortex_scheme"

const BRANCHES = ["AIML"] as const
const SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8] as const

function isValidStoredSelection(value: unknown): value is SchemeSelection {
  if (!value || typeof value !== "object") return false
  const v = value as Record<string, unknown>
  return (
    (v.scheme === "2019" || v.scheme === "2024") &&
    typeof v.branch === "string" &&
    typeof v.semester === "number"
  )
}

function isCompleteSelection(sel: SchemeSelection | null): sel is SchemeSelection {
  if (!sel) return false
  return (
    (sel.scheme === "2019" || sel.scheme === "2024") &&
    sel.branch.trim().length > 0 &&
    Number.isInteger(sel.semester) &&
    sel.semester >= 1 &&
    sel.semester <= 8
  )
}

export function SchemeSelector() {
  const [selection, setSelection] = React.useState<SchemeSelection | null>(null)
  const [locked, setLocked] = React.useState(false)
  const router = useRouter()
  const didRedirectRef = React.useRef(false)

  React.useEffect(() => {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return
    try {
      const parsed: unknown = JSON.parse(raw)
      if (isValidStoredSelection(parsed)) {
        setSelection(parsed)
        setLocked(true)
      }
    } catch {
      // ignore malformed storage
    }
  }, [])

  React.useEffect(() => {
    if (!locked && isCompleteSelection(selection)) {
      // eslint-disable-next-line no-console
      console.log({
        scheme: selection.scheme,
        branch: selection.branch,
        semester: selection.semester,
      })

      const scheme = selection.scheme
      const branch = selection.branch
      const semester = selection.semester

      const upsertPromise = supabase
        .from("users")
        .upsert(
          {
            email: "temp_user@mu-cortex.local",
            scheme_id: scheme,
            branch: branch,
            semester: semester,
          },
          {
            onConflict: "email",
          }
        )
        .then(({ error }) => {
          if (error) {
            // eslint-disable-next-line no-console
            console.error("Supabase insert error")
            // eslint-disable-next-line no-console
            console.error("Message:", error.message)
            // eslint-disable-next-line no-console
            console.error("Details:", error.details)
            // eslint-disable-next-line no-console
            console.error("Hint:", error.hint)
            // eslint-disable-next-line no-console
            console.error("Code:", error.code)
            return
          }
          // eslint-disable-next-line no-console
          console.log("User scheme saved to Supabase")
        })
        .catch((error: unknown) => {
          // eslint-disable-next-line no-console
          console.error("Supabase insert error", error)
        })

      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(selection))
      setLocked(true)

      void upsertPromise.finally(() => {
        if (didRedirectRef.current) return
        didRedirectRef.current = true
        router.push("/dashboard")
      })
    }
  }, [locked, selection])

  const label = selection
    ? `${selection.scheme} • ${selection.branch} • Sem ${selection.semester}`
    : "Select scheme / branch / semester"

  const setScheme = (scheme: Scheme) => {
    setSelection((prev) => ({
      scheme,
      branch: prev?.branch ?? "",
      semester: prev?.semester ?? 0,
    }))
  }

  const setBranch = (branch: string) => {
    setSelection((prev) => ({
      scheme: prev?.scheme ?? "2019",
      branch,
      semester: prev?.semester ?? 0,
    }))
  }

  const setSemester = (semester: number) => {
    setSelection((prev) => ({
      scheme: prev?.scheme ?? "2019",
      branch: prev?.branch ?? "",
      semester,
    }))
  }

  const resetSelection = () => {
    window.localStorage.removeItem(STORAGE_KEY)
    setSelection(null)
    setLocked(false)
    didRedirectRef.current = false
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild disabled={locked}>
            <Button
              variant="outline"
              className="w-full justify-between"
              aria-disabled={locked}
            >
              <span className="truncate">{label}</span>
              <ChevronDown className="h-4 w-4 opacity-70" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-80">
            <DropdownMenuLabel>Scheme</DropdownMenuLabel>
            <DropdownMenuItem onClick={() => setScheme("2019")}>
              2019
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setScheme("2024")}>
              2024
            </DropdownMenuItem>

            <DropdownMenuSeparator />
            <DropdownMenuLabel>Branch</DropdownMenuLabel>
            {BRANCHES.map((b) => (
              <DropdownMenuItem
                key={b}
                onClick={() => setBranch(b)}
              >
                {b}
              </DropdownMenuItem>
            ))}

            <DropdownMenuSeparator />
            <DropdownMenuLabel>Semester</DropdownMenuLabel>
            {SEMESTERS.map((sem) => (
              <DropdownMenuItem
                key={sem}
                onClick={() => setSemester(sem)}
              >
                Semester {sem}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {locked ? (
          <div className="flex items-center gap-2">
            <Badge>Locked</Badge>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-xs text-muted-foreground"
              onClick={resetSelection}
            >
              Reset
            </Button>
          </div>
        ) : null}
      </div>

      <p className="text-xs text-muted-foreground">
        Changing scheme later will reset your progress
      </p>
    </div>
  )
}

