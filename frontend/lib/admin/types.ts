import type { ComponentSummary, Image } from "@/lib/vault/types";

export type AdminItemKind = "component" | "image";

export type AdminComponent = ComponentSummary;

export type AdminImage = Image;

export interface AdminItem {
  id: string;
  kind: AdminItemKind;
  slug: string;
  title: string;
  description: string;
  author: string | null;
  created_at: string;
  /** Cloudinary public id for the picture or the block render. */
  path: string | null;
  width: number | null;
  height: number | null;
}

export interface AdminDeletion {
  id: string;
  kind: AdminItemKind;
  target_id: string;
  slug: string;
  title: string;
  actor: string | null;
  paths: string[];
  result: "deleted" | "failed";
  error: string | null;
  created_at: string;
}

export interface AdminUser {
  id: string;
  supabase_user_id: string;
  email: string | null;
  full_name: string | null;
  banned_at: string | null;
  banned_by: string | null;
  ban_reason: string | null;
  created_at: string;
}
