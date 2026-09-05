import { Routes, Route } from 'react-router-dom'
import { Toaster } from '@/components/ui/sonner'
import { AuthProvider } from '@/lib/AuthContext'
import ProtectedRoute from '@/components/ProtectedRoute'
import ScrollToTop from '@/components/ScrollToTps'
import { ROUTES } from '@/lib/app-params'
import PageNotFound from '@/lib/PageNotFound'
import Home from '@/Pages/Home'
import Login from '@/Pages/Login'
import Register from '@/Pages/Register'
import ForgotPassword from '@/Pages/ForgotPassword'
import ResetPassword from '@/Pages/ResetPassword'
import Preferences from '@/Pages/Preferences'
import Alert from '@/Pages/Alert'
import Map from '@/Pages/Map'
import TabLayout from '@/components/TabLayout'

function App() {
  return (
    <AuthProvider>
      <ScrollToTop />
      <Toaster />
      <Routes>
        <Route path={ROUTES.login} element={<Login />} />
        <Route path={ROUTES.signup} element={<Register />} />
        <Route path={ROUTES.forgotPassword} element={<ForgotPassword />} />
        <Route path={ROUTES.resetPassword} element={<ResetPassword />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<TabLayout />}>
            <Route path={ROUTES.home} element={<Home />} />
            <Route path={ROUTES.map} element={<Map />} />
          </Route>
          <Route path={ROUTES.preferences} element={<Preferences />} />
          <Route path={ROUTES.alert} element={<Alert />} />
        </Route>

        <Route path="*" element={<PageNotFound />} />
      </Routes>
    </AuthProvider>
  )
}

export default App
