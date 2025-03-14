

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE EXTENSION IF NOT EXISTS "pgsodium";






COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgjwt" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE TYPE "public"."character_class" AS ENUM (
    'death-knight',
    'demon-hunter',
    'druid',
    'evoker',
    'hunter',
    'mage',
    'monk',
    'paladin',
    'priest',
    'rogue',
    'shaman',
    'warlock',
    'warrior'
);


ALTER TYPE "public"."character_class" OWNER TO "postgres";


CREATE TYPE "public"."game_region" AS ENUM (
    'us',
    'eu',
    'kr',
    'tw',
    'cn'
);


ALTER TYPE "public"."game_region" OWNER TO "postgres";


CREATE TYPE "public"."game_version" AS ENUM (
    'classic',
    'tbc-classic',
    'wrath-classic',
    'cata-classic',
    'retail'
);


ALTER TYPE "public"."game_version" OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_watched_characters"() RETURNS TABLE("id" "uuid", "version" "public"."game_version", "region" "public"."game_region", "realm" "text", "name" "text")
    LANGUAGE "plpgsql"
    AS $$
BEGIN
  RETURN QUERY
  SELECT DISTINCT ON (c.id) c.id, c.version, c.region, c.realm, c.name
  FROM public.character c
  INNER JOIN public.character_watch_chat_telegram cwct
  ON c.id = cwct.character_id;
END;
$$;


ALTER FUNCTION "public"."get_watched_characters"() OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."character" (
    "realm" "text" NOT NULL,
    "name" "text" NOT NULL,
    "level" integer,
    "online" boolean,
    "zone" "text",
    "died_at" timestamp with time zone,
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "version" "public"."game_version" NOT NULL,
    "region" "public"."game_region" NOT NULL,
    "class" "public"."character_class"
);


ALTER TABLE "public"."character" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."character_watch_chat_telegram" (
    "chat_id" bigint NOT NULL,
    "character_id" "uuid" NOT NULL,
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL
);


ALTER TABLE "public"."character_watch_chat_telegram" OWNER TO "postgres";


ALTER TABLE ONLY "public"."character"
    ADD CONSTRAINT "character_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."character"
    ADD CONSTRAINT "character_version_region_realm_name_key" UNIQUE ("version", "region", "realm", "name");



ALTER TABLE ONLY "public"."character_watch_chat_telegram"
    ADD CONSTRAINT "character_watch_chat_telegram_chat_id_character_id_key" UNIQUE ("chat_id", "character_id");



ALTER TABLE ONLY "public"."character_watch_chat_telegram"
    ADD CONSTRAINT "character_watch_chat_telegram_pkey" PRIMARY KEY ("id");



CREATE INDEX "idx_character_watch_character_id" ON "public"."character_watch_chat_telegram" USING "btree" ("character_id");



CREATE INDEX "idx_characters_class" ON "public"."character" USING "btree" ("class");



CREATE INDEX "idx_characters_name" ON "public"."character" USING "btree" ("name");



CREATE INDEX "idx_characters_realm" ON "public"."character" USING "btree" ("realm");



CREATE INDEX "idx_characters_region" ON "public"."character" USING "btree" ("region");



CREATE INDEX "idx_characters_version" ON "public"."character" USING "btree" ("version");



CREATE INDEX "idx_characters_vrr_name" ON "public"."character" USING "btree" ("version", "region", "realm", "name");



ALTER TABLE ONLY "public"."character_watch_chat_telegram"
    ADD CONSTRAINT "character_watch_chat_telegram_character_id_fkey" FOREIGN KEY ("character_id") REFERENCES "public"."character"("id") ON DELETE CASCADE;



ALTER TABLE "public"."character" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."character_watch_chat_telegram" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";




















































































































































































GRANT ALL ON FUNCTION "public"."get_watched_characters"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_watched_characters"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_watched_characters"() TO "service_role";


















GRANT ALL ON TABLE "public"."character" TO "anon";
GRANT ALL ON TABLE "public"."character" TO "authenticated";
GRANT ALL ON TABLE "public"."character" TO "service_role";



GRANT ALL ON TABLE "public"."character_watch_chat_telegram" TO "anon";
GRANT ALL ON TABLE "public"."character_watch_chat_telegram" TO "authenticated";
GRANT ALL ON TABLE "public"."character_watch_chat_telegram" TO "service_role";



ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "service_role";






























RESET ALL;
