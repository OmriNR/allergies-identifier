// Internal infrastructure shared by the api/ modules. Not part of the public
// api surface — pages should never import this directly, only the domain
// files (users, userProperties, alerts, authentication).
//
// Every domain function is async and returns/throws the same shapes a real
// HTTP client would (data or ApiError), so swapping this mock storage for
// real network calls later shouldn't require changing any call sites.

export class ApiError extends Error {
  status: number;

  constructor(message: string, status = 400) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const STORAGE_PREFIX = "mock-api:";

export function delay<T>(value: T, ms = 300): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

export function generateId(): string {
  return crypto.randomUUID();
}

export function generateToken(): string {
  return crypto.randomUUID().replace(/-/g, "");
}

export function generateCode(): string {
  return String(Math.floor(100000 + Math.random() * 900000));
}

export function readCollection<T>(name: string, seed: T[]): T[] {
  const raw = localStorage.getItem(STORAGE_PREFIX + name);
  if (!raw) {
    localStorage.setItem(STORAGE_PREFIX + name, JSON.stringify(seed));
    return seed;
  }
  try {
    return JSON.parse(raw) as T[];
  } catch {
    return seed;
  }
}

export function writeCollection<T>(name: string, items: T[]): void {
  localStorage.setItem(STORAGE_PREFIX + name, JSON.stringify(items));
}
