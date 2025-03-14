import type { Database } from "../types/db"
import { createClient } from "@supabase/supabase-js"

if (!process.env.SUPABASE_URL || !process.env.SUPABASE_KEY) {
  throw new Error("Missing SUPABASE_URL or SUPABASE_KEY in environment")
}

export const supabase = createClient<Database>(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_KEY,
)
