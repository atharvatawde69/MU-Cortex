-- =========================================================
-- Mumbai University Exam Prep Platform - PostgreSQL Schema
-- =========================================================
-- Notes:
-- - Uses UUID primary keys with uuid_generate_v4()
-- - All tables include scheme_id (2019 or 2024)
-- - created_at / updated_at managed via trigger
-- - Foreign keys use ON DELETE CASCADE where applicable
-- - Indexes added on frequently queried columns
-- =========================================================

-- ==========================
-- Extensions & Prerequisites
-- ==========================

-- UUID generation extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ==========================
-- Timestamp Helper Function
-- ==========================

-- Generic function to auto-update updated_at columns
CREATE OR REPLACE FUNCTION set_updated_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ==================================
-- Table: users
-- ==================================

CREATE TABLE IF NOT EXISTS public.users (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email       TEXT NOT NULL UNIQUE,
  full_name   TEXT,
  branch      TEXT NOT NULL, -- e.g., CS, IT, EXTC
  semester    INTEGER NOT NULL CHECK (semester BETWEEN 1 AND 8),
  scheme_id   TEXT NOT NULL CHECK (scheme_id IN ('2019', '2024')),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.users IS
  'End users preparing for Mumbai University exams. Stores basic profile and academic info.';

-- Indexes for users
CREATE INDEX IF NOT EXISTS idx_users_scheme_id ON public.users (scheme_id);
CREATE INDEX IF NOT EXISTS idx_users_branch_semester ON public.users (branch, semester);

-- Trigger for users.updated_at
CREATE TRIGGER trg_users_set_updated_at
BEFORE UPDATE ON public.users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_timestamp();

-- Enable Row Level Security (policies to be added later)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;


-- ==================================
-- Table: subjects
-- ==================================

CREATE TABLE IF NOT EXISTS public.subjects (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name            TEXT NOT NULL,
  code            TEXT NOT NULL,
  scheme_id       TEXT NOT NULL CHECK (scheme_id IN ('2019', '2024')),
  semester        INTEGER NOT NULL CHECK (semester BETWEEN 1 AND 8),
  branch          TEXT NOT NULL,
  syllabus_pdf_url TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_subjects_code_scheme UNIQUE (code, scheme_id)
);

COMMENT ON TABLE public.subjects IS
  'Subjects offered under different schemes, branches, and semesters (e.g., Operating Systems, DBMS).';

-- Indexes for subjects
CREATE INDEX IF NOT EXISTS idx_subjects_scheme_id ON public.subjects (scheme_id);
CREATE INDEX IF NOT EXISTS idx_subjects_branch_semester ON public.subjects (branch, semester);
CREATE INDEX IF NOT EXISTS idx_subjects_code ON public.subjects (code);

-- Trigger for subjects.updated_at
CREATE TRIGGER trg_subjects_set_updated_at
BEFORE UPDATE ON public.subjects
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_timestamp();


-- ==================================
-- Table: topics
-- ==================================

CREATE TABLE IF NOT EXISTS public.topics (
  id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  subject_id     UUID NOT NULL REFERENCES public.subjects(id) ON DELETE CASCADE,
  name           TEXT NOT NULL,
  module_number  INTEGER CHECK (module_number BETWEEN 1 AND 6),
  scheme_id      TEXT NOT NULL CHECK (scheme_id IN ('2019', '2024')),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.topics IS
  'Fine-grained topics within a subject, typically mapped to MU modules (e.g., Deadlock Prevention).';

-- Indexes for topics
CREATE INDEX IF NOT EXISTS idx_topics_subject_id ON public.topics (subject_id);
CREATE INDEX IF NOT EXISTS idx_topics_scheme_id ON public.topics (scheme_id);
CREATE INDEX IF NOT EXISTS idx_topics_subject_module ON public.topics (subject_id, module_number);

-- Trigger for topics.updated_at
CREATE TRIGGER trg_topics_set_updated_at
BEFORE UPDATE ON public.topics
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_timestamp();


-- ==================================
-- Table: video_resources
-- ==================================

CREATE TABLE IF NOT EXISTS public.video_resources (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  topic_id          UUID NOT NULL REFERENCES public.topics(id) ON DELETE CASCADE,
  youtube_url       TEXT NOT NULL UNIQUE,
  youtube_video_id  TEXT NOT NULL,
  channel_name      TEXT NOT NULL,
  title             TEXT NOT NULL,
  view_count        BIGINT NOT NULL DEFAULT 0,
  comment_count     INTEGER NOT NULL DEFAULT 0,
  engagement_score  BIGINT GENERATED ALWAYS AS (view_count + comment_count) STORED,
  scheme_id         TEXT NOT NULL CHECK (scheme_id IN ('2019', '2024')),
  last_fetched      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  is_restricted     BOOLEAN NOT NULL DEFAULT FALSE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.video_resources IS
  'YouTube video resources mapped to topics, with basic engagement metrics and restrictions.';

-- Indexes for video_resources
CREATE INDEX IF NOT EXISTS idx_video_resources_topic_id ON public.video_resources (topic_id);
CREATE INDEX IF NOT EXISTS idx_video_resources_scheme_id ON public.video_resources (scheme_id);
CREATE INDEX IF NOT EXISTS idx_video_resources_youtube_video_id ON public.video_resources (youtube_video_id);
CREATE INDEX IF NOT EXISTS idx_video_resources_channel_name ON public.video_resources (channel_name);

-- Trigger for video_resources.updated_at
CREATE TRIGGER trg_video_resources_set_updated_at
BEFORE UPDATE ON public.video_resources
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_timestamp();


-- ==================================
-- Table: predicted_questions
-- ==================================

CREATE TABLE IF NOT EXISTS public.predicted_questions (
  id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  topic_id         UUID NOT NULL REFERENCES public.topics(id) ON DELETE CASCADE,
  question_text    TEXT NOT NULL,
  marks            INTEGER NOT NULL CHECK (marks IN (2, 5, 10)),
  frequency_score  INTEGER NOT NULL DEFAULT 0,
  last_appeared    TEXT,
  scheme_id        TEXT NOT NULL CHECK (scheme_id IN ('2019', '2024')),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.predicted_questions IS
  'AI / expert predicted exam questions per topic, with marks, frequency, and last appearance metadata.';

-- Indexes for predicted_questions
CREATE INDEX IF NOT EXISTS idx_predicted_questions_topic_id ON public.predicted_questions (topic_id);
CREATE INDEX IF NOT EXISTS idx_predicted_questions_scheme_id ON public.predicted_questions (scheme_id);
CREATE INDEX IF NOT EXISTS idx_predicted_questions_marks ON public.predicted_questions (marks);

-- Trigger for predicted_questions.updated_at
CREATE TRIGGER trg_predicted_questions_set_updated_at
BEFORE UPDATE ON public.predicted_questions
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_timestamp();


-- ==================================
-- Table: channel_whitelist
-- ==================================

CREATE TABLE IF NOT EXISTS public.channel_whitelist (
  id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  channel_id     TEXT NOT NULL UNIQUE, -- YouTube channel ID
  channel_name   TEXT NOT NULL,
  channel_handle TEXT,
  priority       INTEGER NOT NULL DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
  added_by       TEXT NOT NULL DEFAULT 'admin' CHECK (added_by IN ('admin', 'community')),
  status         TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'deleted', 'suspended')),
  scheme_id      TEXT NOT NULL CHECK (scheme_id IN ('2019', '2024')),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.channel_whitelist IS
  'Curated list of YouTube channels allowed for sourcing educational content, with moderation status and priority.';

-- Indexes for channel_whitelist
CREATE INDEX IF NOT EXISTS idx_channel_whitelist_channel_id ON public.channel_whitelist (channel_id);
CREATE INDEX IF NOT EXISTS idx_channel_whitelist_scheme_id ON public.channel_whitelist (scheme_id);
CREATE INDEX IF NOT EXISTS idx_channel_whitelist_status_priority ON public.channel_whitelist (status, priority);

-- Trigger for channel_whitelist.updated_at
CREATE TRIGGER trg_channel_whitelist_set_updated_at
BEFORE UPDATE ON public.channel_whitelist
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_timestamp();


-- ==========================
-- Additional Helpful Comments
-- ==========================

COMMENT ON COLUMN public.video_resources.engagement_score IS
  'Precomputed engagement metric: view_count + comment_count.';

COMMENT ON COLUMN public.predicted_questions.frequency_score IS
  'Number of times this or a very similar question has appeared in past MU exams.';

COMMENT ON COLUMN public.predicted_questions.last_appeared IS
  'Human-readable label for the last exam this question appeared in, e.g., "Dec 2023".';

