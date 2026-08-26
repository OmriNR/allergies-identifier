import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import * as usersApi from "@/api/users"
import * as authApi from "@/api/authentication"
import type { User } from "@/api/users"

export type AuthUser = User

interface AuthContextValue {
  user: AuthUser | null
  isLoading: boolean
  login: (user: AuthUser, token: string) => void
  logout: () => Promise<void>
  updateUser: (data: Partial<Pick<AuthUser, "name" | "avatarUrl" | "email">>) => Promise<void>
}

const TOKEN_STORAGE_KEY = "auth:token"

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (!storedToken) {
      setIsLoading(false)
      return
    }

    authApi.getSession(storedToken).then(async (session) => {
      if (!session) {
        localStorage.removeItem(TOKEN_STORAGE_KEY)
        setIsLoading(false)
        return
      }
      const restoredUser = await usersApi.getUser(session.userId)
      if (restoredUser) {
        setUser(restoredUser)
        setToken(storedToken)
      } else {
        localStorage.removeItem(TOKEN_STORAGE_KEY)
      }
      setIsLoading(false)
    })
  }, [])

  function login(nextUser: AuthUser, nextToken: string) {
    localStorage.setItem(TOKEN_STORAGE_KEY, nextToken)
    setToken(nextToken)
    setUser(nextUser)
  }

  async function logout() {
    if (token) {
      await authApi.invalidateToken(token)
    }
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    setToken(null)
    setUser(null)
  }

  async function updateUser(data: Partial<Pick<AuthUser, "name" | "avatarUrl" | "email">>) {
    if (!user) return
    const updated = await usersApi.updateUser(user.id, data)
    setUser(updated)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
