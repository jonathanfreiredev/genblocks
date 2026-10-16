import "server-only";

import { env } from "@/lib/env";
import type {
  Category,
  Component,
  ComponentSummary,
  Generation,
  Image,
  OffsetPage,
  Task,
  TaskDetail,
} from "@/lib/vault/types";

/**
 * Raised when the vault cannot be read at all.
 *
 * Server-only and deliberately narrow: the pages catch it and render a surface
 * that names the problem and the way out, instead of handing a stack trace to
 * someone who only wanted to browse.
 */
export class VaultUnreadable extends Error {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "VaultUnreadable";
  }
}

type Query = Record<string, string | number | undefined>;

/**
 * The one place the browser never sees: every read below happens on the server,
 * and the calls that need a caller carry the session's own access token.
 */
async function request(
  path: string,
  query: Query,
  token?: string,
): Promise<Response> {
  const url = new URL(`/v1${path}`, env.BACKEND_URL);

  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }

  const headers: Record<string, string> = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  try {
    // No caching: the vault is a few hundred rows behind one indexed query, and
    // a stale gallery is a worse trade than the round trip.
    return await fetch(url, { headers, cache: "no-store" });
  } catch (cause) {
    throw new VaultUnreadable(
      `The vault API at ${url.origin} did not answer.`,
      { cause },
    );
  }
}

async function read<T>(
  path: string,
  query: Query = {},
  token?: string,
): Promise<T> {
  const response = await request(path, query, token);

  if (!response.ok) {
    throw new VaultUnreadable(
      `The vault API answered ${response.status} for ${new URL(response.url).pathname}.`,
    );
  }

  return (await response.json()) as T;
}

async function readOrNull<T>(
  path: string,
  query: Query = {},
  token?: string,
): Promise<T | null> {
  const response = await request(path, query, token);

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new VaultUnreadable(
      `The vault API answered ${response.status} for ${new URL(response.url).pathname}.`,
    );
  }

  return (await response.json()) as T;
}

interface CatalogueQuery {
  categoryId?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

/** The whole taxonomy. Small and fixed, so it arrives in one request. */
export function listCategories(): Promise<Category[]> {
  return read<Category[]>("/categories");
}

export function listComponents(
  query: CatalogueQuery = {},
): Promise<OffsetPage<ComponentSummary>> {
  return read<OffsetPage<ComponentSummary>>("/components", {
    category_id: query.categoryId,
    search: query.search,
    limit: query.limit,
    offset: query.offset,
  });
}

/** One block in full, or `null` when that id names nothing. */
export function getComponent(id: string): Promise<Component | null> {
  return readOrNull<Component>(`/components/${id}`);
}

/** A block's whole attempt history, oldest first. */
export function listComponentGenerations(id: string): Promise<Generation[]> {
  return read<Generation[]>(`/components/${id}/generations`);
}

export function listImages(
  query: CatalogueQuery = {},
): Promise<OffsetPage<Image>> {
  return read<OffsetPage<Image>>("/images", {
    category_id: query.categoryId,
    search: query.search,
    limit: query.limit,
    offset: query.offset,
  });
}

export function getImage(id: string): Promise<Image | null> {
  return readOrNull<Image>(`/images/${id}`);
}

/** The caller's own tasks. The token decides whose they are; nothing else does. */
export function listTasks(
  token: string,
  query: { limit?: number; offset?: number } = {},
): Promise<OffsetPage<Task>> {
  return read<OffsetPage<Task>>(
    "/tasks",
    { limit: query.limit, offset: query.offset },
    token,
  );
}

/** One task with its checklist and its attempts, or `null` if it is not theirs. */
export function getTask(token: string, id: string): Promise<TaskDetail | null> {
  return readOrNull<TaskDetail>(`/tasks/${id}`, {}, token);
}
