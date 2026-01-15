 "use client"

import type { ReactNode } from "react"
import { useRouter } from "next/navigation"

import { Button } from "@/components/ui/button"

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const router = useRouter()

  const onLogout = () => {
    window.localStorage.removeItem("mu_cortex_scheme")
    router.push("/")
  }

  return (
    <div className="min-h-screen">
      <header className="border-b">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <div className="text-sm font-semibold">MU Cortex</div>
          <div className="flex items-center gap-3">
            <div className="text-xs text-muted-foreground">Dashboard (placeholder)</div>
            <Button variant="ghost" size="sm" onClick={onLogout}>
              Logout
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl px-6 py-8">{children}</main>
    </div>
  )
}
