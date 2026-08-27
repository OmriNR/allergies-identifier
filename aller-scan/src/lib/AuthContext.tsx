import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import * as usersApi from "@/api/users"
import { clearStoredToken, getStoredToken, setStoredToken } from "@/api/httpClient"
import type { User } from "@/api/users"

export type AuthUser = User

interface AuthContextValue {
  user: AuthUser | null
  isLoading: boolean
  login: (user: AuthUser, token: string) => void
  logout: () => Promise<void>
  updateUser: (data: Partial<Pick<AuthUser, "name" | "avatarUrl">>) => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const storedToken = getStoredToken()
    if (!storedToken) {
      setIsLoading(false)
      return
    }

    usersApi.getMe(storedToken).then((restoredUser) => {
      if (restoredUser) {
        setUser(restoredUser)
      } else {
        clearStoredToken()
      }
      setIsLoading(false)
    })
  }, [])

  function login(nextUser: AuthUser, nextToken: string) {
    setStoredToken(nextToken)
    setUser(nextUser)
  }

  async function logout() {
    // JWTs are stateless and the backend has no invalidate endpoint, so
    // logging out is purely a client-side token drop.
    clearStoredToken()
    setUser(null)
  }

  async function updateUser(data: Partial<Pick<AuthUser, "name" | "avatarUrl">>) {
    if (!user) return
    const updated = await usersApi.updateUser(data)
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
