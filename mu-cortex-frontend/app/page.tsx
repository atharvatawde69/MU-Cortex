import { SchemeSelector } from "@/components/SchemeSelector"

export default function Home() {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-b from-[#003366] to-[#001a33] px-4">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(255,255,255,0.14),transparent_55%)]" />

      <main className="relative w-full max-w-xl">
        <div className="mb-6 text-center">
          <h1 className="text-balance text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            Your AI Study Partner for Mumbai University Exams
          </h1>
        </div>

        <div className="rounded-2xl border bg-background/90 p-6 shadow-lg backdrop-blur supports-[backdrop-filter]:bg-background/70">
          <div className="mb-4 text-sm font-medium text-foreground/90">
            Select Your Scheme
          </div>
          <SchemeSelector />
        </div>
      </main>
    </div>
  )
}
