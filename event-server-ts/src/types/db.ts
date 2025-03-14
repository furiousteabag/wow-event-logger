export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[]

export type Database = {
  public: {
    Tables: {
      character: {
        Row: {
          class: Database["public"]["Enums"]["character_class"] | null
          died_at: string | null
          id: string
          level: number | null
          name: string
          online: boolean | null
          realm: string
          region: Database["public"]["Enums"]["game_region"]
          version: Database["public"]["Enums"]["game_version"]
          zone: string | null
        }
        Insert: {
          class?: Database["public"]["Enums"]["character_class"] | null
          died_at?: string | null
          id?: string
          level?: number | null
          name: string
          online?: boolean | null
          realm: string
          region: Database["public"]["Enums"]["game_region"]
          version: Database["public"]["Enums"]["game_version"]
          zone?: string | null
        }
        Update: {
          class?: Database["public"]["Enums"]["character_class"] | null
          died_at?: string | null
          id?: string
          level?: number | null
          name?: string
          online?: boolean | null
          realm?: string
          region?: Database["public"]["Enums"]["game_region"]
          version?: Database["public"]["Enums"]["game_version"]
          zone?: string | null
        }
        Relationships: []
      }
      character_watch_chat_telegram: {
        Row: {
          character_id: string
          chat_id: number
          id: string
        }
        Insert: {
          character_id: string
          chat_id: number
          id?: string
        }
        Update: {
          character_id?: string
          chat_id?: number
          id?: string
        }
        Relationships: [
          {
            foreignKeyName: "character_watch_chat_telegram_character_id_fkey"
            columns: ["character_id"]
            isOneToOne: false
            referencedRelation: "character"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      get_watched_characters: {
        Args: Record<PropertyKey, never>
        Returns: {
          class: Database["public"]["Enums"]["character_class"] | null
          died_at: string | null
          id: string
          level: number | null
          name: string
          online: boolean | null
          realm: string
          region: Database["public"]["Enums"]["game_region"]
          version: Database["public"]["Enums"]["game_version"]
          zone: string | null
        }[]
      }
    }
    Enums: {
      character_class:
        | "death-knight"
        | "demon-hunter"
        | "druid"
        | "evoker"
        | "hunter"
        | "mage"
        | "monk"
        | "paladin"
        | "priest"
        | "rogue"
        | "shaman"
        | "warlock"
        | "warrior"
      game_region: "us" | "eu" | "kr" | "tw" | "cn"
      game_version: "classic" | "tbc-classic" | "wrath-classic" | "cata-classic" | "retail"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type PublicSchema = Database[Extract<keyof Database, "public">]

export type Tables<
  PublicTableNameOrOptions extends keyof (PublicSchema["Tables"] & PublicSchema["Views"]) | { schema: keyof Database },
  TableName extends PublicTableNameOrOptions extends { schema: keyof Database }
    ? keyof (Database[PublicTableNameOrOptions["schema"]]["Tables"] &
        Database[PublicTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = PublicTableNameOrOptions extends { schema: keyof Database }
  ? (Database[PublicTableNameOrOptions["schema"]]["Tables"] &
      Database[PublicTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : PublicTableNameOrOptions extends keyof (PublicSchema["Tables"] & PublicSchema["Views"])
    ? (PublicSchema["Tables"] & PublicSchema["Views"])[PublicTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  PublicTableNameOrOptions extends keyof PublicSchema["Tables"] | { schema: keyof Database },
  TableName extends PublicTableNameOrOptions extends { schema: keyof Database }
    ? keyof Database[PublicTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = PublicTableNameOrOptions extends { schema: keyof Database }
  ? Database[PublicTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : PublicTableNameOrOptions extends keyof PublicSchema["Tables"]
    ? PublicSchema["Tables"][PublicTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  PublicTableNameOrOptions extends keyof PublicSchema["Tables"] | { schema: keyof Database },
  TableName extends PublicTableNameOrOptions extends { schema: keyof Database }
    ? keyof Database[PublicTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = PublicTableNameOrOptions extends { schema: keyof Database }
  ? Database[PublicTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : PublicTableNameOrOptions extends keyof PublicSchema["Tables"]
    ? PublicSchema["Tables"][PublicTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  PublicEnumNameOrOptions extends keyof PublicSchema["Enums"] | { schema: keyof Database },
  EnumName extends PublicEnumNameOrOptions extends { schema: keyof Database }
    ? keyof Database[PublicEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = PublicEnumNameOrOptions extends { schema: keyof Database }
  ? Database[PublicEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : PublicEnumNameOrOptions extends keyof PublicSchema["Enums"]
    ? PublicSchema["Enums"][PublicEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends keyof PublicSchema["CompositeTypes"] | { schema: keyof Database },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof Database[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends { schema: keyof Database }
  ? Database[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof PublicSchema["CompositeTypes"]
    ? PublicSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never
