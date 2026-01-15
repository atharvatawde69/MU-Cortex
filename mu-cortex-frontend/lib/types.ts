export type SchemeId = "2019" | "2024"

export interface Subject {
  id: string
  name: string
  code: string
  scheme_id: SchemeId
  semester: number
  branch: string
  syllabus_pdf_url: string | null
  created_at: string
  updated_at: string
}

export interface Topic {
  id: string
  subject_id: string
  name: string
  module_number: number | null
  scheme_id: SchemeId
  created_at: string
  updated_at: string
}

export interface VideoResource {
  id: string
  topic_id: string
  youtube_url: string
  youtube_video_id: string
  channel_name: string
  title: string
  view_count: number
  comment_count: number
  engagement_score: number
  scheme_id: SchemeId
  last_fetched: string
  is_restricted: boolean
  created_at: string
  updated_at: string
}

