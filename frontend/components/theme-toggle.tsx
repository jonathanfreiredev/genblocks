"use client"

import * as React from "react"
import { MoonIcon, SunIcon } from "lucide-react"

import { Button } from "@/components/ui/button"

/**
 * Theme, without a dependency.
 *
 * The source of truth is the `dark` class on `<html>`, set before paint by the
 * inline script in `app/layout.tsx`. This module only reads and writes it, and
 * keeps every mounted toggle in sync through a custom event, so the footer and
 * the mobile sheet never disagree.
 */
export const THEME_STORAGE_KEY = "genblocks-theme"

const THEME_EVENT = "genblocks-theme-change"

export type Theme = "light" | "dark"

function readTheme(): Theme {
  return document.documentElement.classList.contains("dark") ? "dark" : "light"
}

function subscribe(callback: () => void) {
  window.addEventListener(THEME_EVENT, callback)
  return () => window.removeEventListener(THEME_EVENT, callback)
}

function writeTheme(theme: Theme, persist: boolean) {
  document.documentElement.classList.toggle("dark", theme === "dark")

  if (persist) {
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme)
    } catch {
      // Private mode or a full quota: the class above is still applied.
    }
  }

  window.dispatchEvent(new Event(THEME_EVENT))
}

export function useTheme() {
  const theme = React.useSyncExternalStore(
    subscribe,
    readTheme,
    // Server snapshot: `dark` is applied before paint, and this switches to the
    // real value right after hydration without a mismatch warning.
    () => "light" as Theme
  )

  return {
    theme,
    isDark: theme === "dark",
    setTheme: (next: Theme) => writeTheme(next, true),
    toggle: () => writeTheme(readTheme() === "dark" ? "light" : "dark", true),
  }
}

export function ThemeToggle({ className }: { className?: string }) {
  const { isDark, toggle } = useTheme()

  return (
    <Button
      variant="ghost"
      size="icon-sm"
      className={className}
      onClick={toggle}
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
    >
      {isDark ? <MoonIcon /> : <SunIcon />}
    </Button>
  )
}
