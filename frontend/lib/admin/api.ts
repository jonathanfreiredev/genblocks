import "server-only";

import { env } from "@/lib/env";
import type { OffsetPage } from "@/lib/vault/types";
import type {
  AdminComponent,
  AdminDeletion,
  AdminImage,
  AdminItem,
  AdminItemKind,
  AdminUser,
} from "./types";

export class AdminUnreadable extends Error {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "AdminUnreadable";
  }
}

async function request(
  path: string,
  token: string,
  init?: RequestInit,
): Promise<Response> {
  const url = new URL(`/v1${path}`, env.BACKEND_URL);

  try {
    return await fetch(url, {
      ...init,
      headers: {
        Authorization: `Bearer ${token}`,
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
      cache: "no-store",
    });
  } catch (cause) {
    throw new AdminUnreadable(
      `The admin API at ${url.origin} did not answer.`,
      { cause },
    );
  }
}

async function read<T>(path: string, token: string): Promise<T> {
  const response = await request(path, token);

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new AdminUnreadable(
      typeof body.detail === "string"
        ? body.detail
        : `The admin API answered ${response.status}.`,
    );
  }

  return (await response.json()) as T;
}

async function readJson<T>(
  path: string,
  token: string,
  method: "POST",
  body: Record<string, unknown>,
): Promise<T> {
  const response = await request(path, token, {
    method,
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new AdminUnreadable(
      typeof payload.detail === "string"
        ? payload.detail
        : `The admin API answered ${response.status}.`,
    );
  }

  return (await response.json()) as T;
}

async function act(path: string, token: string, method: "DELETE") {
  const response = await request(path, token, { method });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new AdminUnreadable(
      typeof body.detail === "string"
        ? body.detail
        : `The admin API answered ${response.status}.`,
    );
  }
}

function listQuery(input: { search?: string; limit?: number; offset?: number }): string {
  const params = new URLSearchParams();
  if (input.search) params.set("search", input.search);
  if (input.limit) params.set("limit", String(input.limit));
  if (input.offset) params.set("offset", String(input.offset));
  const suffix = params.size ? `?${params}` : "";
  return suffix;
}

export function listAdminComponents(
  token: string,
  input: { search?: string; limit?: number; offset?: number },
): Promise<OffsetPage<AdminComponent>> {
  return read(`/admin/components${listQuery(input)}`, token);
}

export function listAdminImages(
  token: string,
  input: { search?: string; limit?: number; offset?: number },
): Promise<OffsetPage<AdminImage>> {
  return read(`/admin/images${listQuery(input)}`, token);
}

export function listAdminDeletions(
  token: string,
  limit = 20,
): Promise<AdminDeletion[]> {
  return read(`/admin/deletions?limit=${limit}`, token);
}

export function listAdminUsers(
  token: string,
  input: { search?: string; limit?: number; offset?: number },
): Promise<AdminUser[]> {
  return read(`/admin/users${listQuery(input)}`, token);
}

export function getAdminUser(token: string, id: string): Promise<AdminUser> {
  return read(`/admin/users/${id}`, token);
}

export function banAdminUser(
  token: string,
  id: string,
  reason?: string,
): Promise<AdminUser> {
  return readJson(`/admin/users/${id}/ban`, token, "POST", { reason });
}

export function unbanAdminUser(token: string, id: string): Promise<AdminUser> {
  return readJson(`/admin/users/${id}/unban`, token, "POST", {});
}

export function deleteAdminItem(
  token: string,
  kind: AdminItemKind,
  id: string,
): Promise<void> {
  return act(`/admin/${kind}s/${id}`, token, "DELETE");
}

export function asAdminItem(
  kind: AdminItemKind,
  item: AdminComponent | AdminImage,
): AdminItem {
  if (kind === "component") {
    const component = item as AdminComponent;
    return {
      id: component.id,
      kind,
      slug: component.slug,
      title: component.title,
      description: component.description,
      author: component.author,
      created_at: component.created_at,
      path: component.screenshot_path,
      width: null,
      height: null,
    };
  }

  const image = item as AdminImage;
  return {
    id: image.id,
    kind,
    slug: image.slug ?? image.id,
    title: image.prompt,
    description: image.prompt,
    author: image.author,
    created_at: image.created_at,
    path: image.path,
    width: image.width,
    height: image.height,
  };
}
