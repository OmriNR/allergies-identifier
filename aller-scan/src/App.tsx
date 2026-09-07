import { Toaster } from "@/components/ui/sonner";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/query-client";
import {
  BrowserRouter as Router,
  Route,
  Routes,
} from "react-router-dom";
import PageNotFound from "./lib/PageNotFound";
import { AuthProvider, useAuth } from "@/lib/AuthContext";
import ScrollToTop from "./components/ScrollToTps";
import ProtectedRoute from "@/components/ProtectedRoute";
import Login from "./Pages/Login";
import Register from "./Pages/Register"
import ForgotPassword from "./Pages/ForgotPassword";
import ResetPassword from "./Pages/ResetPassword";
import Home from "./Pages/Home";
import Preferences from "./Pages/Preferences";
import Alert from "./Pages/Alert";
import AppTabLayout from "@/components/AppTabLayout";
import Resteraunts from "./Pages/Resteraunts";
import AddRestaurant from "./Pages/AddResteraunt";
import ResterauntProfile from "./Pages/ResterauntProfile";

const AuthenticatedApp = () => {
  const { isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="fixed inset-0 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-slate-200 border-t-slate-800 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppTabLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/restaurants" element={<Resteraunts />} />
          <Route path="/preferences" element={<Preferences />} />
        </Route>
        <Route path="/alert" element={<Alert />} />
        <Route path="/restaurants/new" element={<AddRestaurant />} />
        <Route path="/restaurants/:id" element={<ResterauntProfile />} />
      </Route>
      <Route path="*" element={<PageNotFound />} />
    </Routes>
  );
};

function App() {
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <div className="min-h-screen bg-neutral-200">
          <div className="mx-auto min-h-screen max-w-md bg-background shadow-xl">
            <Router>
              <ScrollToTop />
              <AuthenticatedApp />
            </Router>
          </div>
        </div>
        <Toaster />
      </QueryClientProvider>
    </AuthProvider>
  );
}

export default App;