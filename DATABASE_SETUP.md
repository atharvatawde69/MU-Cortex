# MU-Cortex Database Setup

## Supabase Credentials
- Project URL: [REDACTED – share via secure channel]
- Anon Key: [REDACTED]
- Service Role Key: [REDACTED – NEVER commit to Git]

⚠️ Keys must be shared privately (Slack DM / encrypted chat).

---

## Database Schema
We currently have the following tables:

1. users  
   Student profiles tied to branch, semester, and scheme.

2. subjects  
   Subjects offered per scheme, semester, and branch.

3. topics  
   Individual syllabus topics mapped to subjects.

4. video_resources  
   YouTube videos mapped to topics (not populated yet).

5. predicted_questions  
   AI / PYQ-based predicted questions (not populated yet).

6. channel_whitelist  
   Approved YouTube channels (not populated yet).

---

## Current Data Status
- ✅ 5 subjects imported (AIML Sem V & VI, 2019 scheme)
- ✅ 30 topics mapped correctly
- ❌ video_resources not populated yet
- ❌ channel_whitelist not populated yet

---

## For Frontend Team (Person A)

Use the **ANON KEY only**.

Example (JavaScript):

```js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
)

const { data } = await supabase
  .from('subjects')
  .select('*')
  .eq('scheme_id', '2019')
  .eq('semester', 5)

For Backend Team (Person B)

Use the SERVICE ROLE KEY
⚠️ Backend only. Never expose to frontend.

Use for:

Admin queries

Seeding

RLS bypass

Background jobs

Next Steps

 Person D: Populate channel_whitelist

 Person D: Populate video_resources

 Person A: Build subject → topic UI

 Person B: Create /subjects and /topics API endpoints

 Person C: Extend syllabus coverage