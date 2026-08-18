import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { ROUTES } from "@/lib/app-params"

export default function PageNotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4 text-center">
      <p className="text-sm font-medium text-muted-foreground">404</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight text-foreground">
        Page not found
      </h1>
      <p className="mt-2 text-muted-foreground">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Button asChild className="mt-6">
        <Link to={ROUTES.home}>Back to home</Link>
      </Button>
    </div>
  )
}
