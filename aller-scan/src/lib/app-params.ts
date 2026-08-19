export const APP_NAME = "AllerScan"

export const ROUTES = {
  home: "/",
  login: "/login",
  signup: "/register",
  forgotPassword: "/forgot-password",
  resetPassword: "/reset-password",
  preferences: "/preferences",
  alert: "/alert",
} as const

export const QUERY_PARAMS = {
  returnTo: "returnTo",
} as const
