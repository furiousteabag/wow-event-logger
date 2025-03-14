import { includeIgnoreFile } from "@eslint/compat"
import js from "@eslint/js"
import tsPlugin from "@typescript-eslint/eslint-plugin"
import parser from "@typescript-eslint/parser"
import prettier from "eslint-config-prettier"
import { defineConfig } from "eslint/config"
import path from "node:path"
import { fileURLToPath } from "node:url"

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const gitignorePath = path.resolve(__dirname, ".gitignore")

export default defineConfig([
  js.configs.recommended,

  includeIgnoreFile(gitignorePath),

  {
    files: ["**/*.ts"],
    languageOptions: {
      parser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
      },
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
    },
    rules: {
      ...tsPlugin.configs["recommended"].rules,
    },
  },

  {
    rules: {
      ...prettier.rules,
      "no-undef": "off",
    },
  },
])
