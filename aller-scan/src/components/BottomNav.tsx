import { NavLink } from "react-router-dom";
import { ScanLine, MapPin } from "lucide-react";
import { ROUTES } from "@/lib/app-params";

const TABS = [
  { to: ROUTES.home, label: "Scan", icon: ScanLine },
  { to: ROUTES.map, label: "Map", icon: MapPin },
];

export default function BottomNav() {
  return (
    <nav className="shrink-0 border-t border-border bg-card">
      <div className="mx-auto flex max-w-md items-stretch justify-around px-2 pb-[env(safe-area-inset-bottom)] pt-1">
        {TABS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end
            className={({ isActive }) =>
              "flex flex-1 flex-col items-center gap-1 rounded-xl px-3 py-2 text-xs font-medium transition-colors " +
              (isActive ? "text-primary" : "text-muted-foreground hover:text-foreground")
            }
          >
            <Icon className="h-5 w-5" />
            {label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
