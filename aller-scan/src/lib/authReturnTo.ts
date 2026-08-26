import { ROUTES } from "@/lib/app-params"

const STORAGE_KEY = "auth:returnTo"

export function saveReturnTo(path: string) {
  if (path && path !== ROUTES.login && path !== ROUTES.signup) {
    sessionStorage.setItem(STORAGE_KEY, path)
  }
}

export function getReturnTo(fallback: string = ROUTES.home) {
  return sessionStorage.getItem(STORAGE_KEY) ?? fallback
}

export function clearReturnTo() {
  sessionStorage.removeItem(STORAGE_KEY)
}
