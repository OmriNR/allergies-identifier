import { NavLink } from "react-router-dom";
import { ScanLine, UtensilsCrossed, HeartPulse } from "lucide-react";

const TABS = [
  { to: "/", label: "Scan", icon: ScanLine },
  { to: "/restaurants", label: "Restaurants", icon: UtensilsCrossed },
  { to: "/preferences", label: "Allergies", icon: HeartPulse },
];

export default function TabBar() {
  return (
    <nav className="sticky bottom-0 z-[1000] h-16 border-t border-border bg-background/95 backdrop-blur">
      <div className="grid h-full grid-cols-3">
        {TABS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              "flex flex-col items-center justify-center gap-1 text-[11px] font-medium transition-colors " +
              (isActive
                ? "text-primary"
                : "text-muted-foreground hover:text-foreground")
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