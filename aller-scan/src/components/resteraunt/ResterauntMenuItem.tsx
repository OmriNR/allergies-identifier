import { AlertTriangle, Check } from "lucide-react";
import type { MenuItem } from "@/api/resteraunts";

interface RestaurantMenuItemProps {
  item: MenuItem;
  allergies: string[];
}

export default function RestaurantMenuItem({ item, allergies }: RestaurantMenuItemProps) {
  const lower = allergies.map((a) => a.toLowerCase());
  const matched = item.allergens.filter((a) => lower.includes(a.toLowerCase()));
  const unsafe = allergies.length > 0 && matched.length > 0;

  return (
    <div
      className={
        "rounded-xl border p-3.5 " +
        (unsafe ? "border-red-200 bg-red-50" : "border-border bg-card")
      }
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium">{item.item_name}</p>
          {item.ingredients.length > 0 && (
            <p className="mt-0.5 text-xs text-muted-foreground">
              {item.ingredients.join(", ")}
            </p>
          )}
          {item.allergens.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {item.allergens.map((a) => (
                <span
                  key={a}
                  className={
                    "rounded-full px-2 py-0.5 text-[11px] font-medium " +
                    (matched.includes(a)
                      ? "bg-red-100 text-red-700"
                      : "bg-muted text-muted-foreground")
                  }
                >
                  {a}
                </span>
              ))}
            </div>
          )}
        </div>
        {allergies.length > 0 &&
          (unsafe ? (
            <div className="flex shrink-0 items-center gap-1 rounded-full bg-red-100 px-2 py-1 text-[11px] font-medium text-red-700">
              <AlertTriangle className="h-3.5 w-3.5" /> Unsafe
            </div>
          ) : (
            <div className="flex shrink-0 items-center gap-1 rounded-full bg-emerald-100 px-2 py-1 text-[11px] font-medium text-emerald-700">
              <Check className="h-3.5 w-3.5" /> Safe
            </div>
          ))}
      </div>
    </div>
  );
}