import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Clock, Globe, Loader2, MapPin } from "lucide-react";
import type { MenuItem, Resteraunt } from "@/api/resteraunts";
import { getResteraunt } from "@/api/resteraunts";
import { getAllergies } from "@/api/userProperties";
import { useAuth } from "@/lib/AuthContext";
import RestaurantMenuItem from "@/components/resteraunt/ResterauntMenuItem";

export default function ResterauntProfile() {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();
    const [restaurant, setRestaurant] = useState<Resteraunt | null>(null);
    const [allergies, setAllergies] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!id) {
            setLoading(false);
            return;
        }

        Promise.all([
            getResteraunt(id).catch(() => null),
            user ? getAllergies(user.id).catch(() => []) : Promise.resolve([]),
        ])
            .then(([foundRestaurant, userAllergies]) => {
                setRestaurant(foundRestaurant);
                setAllergies(userAllergies);
            })
            .finally(() => setLoading(false));
    }, [id, user]);

    if (loading) {
        return (
            <div className="flex min-h-[60vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    if (!restaurant) {
        return (
            <div className="mx-auto max-w-md px-5 py-10 text-center">
                <p className="text-sm text-muted-foreground">Restaurant not found.</p>
                <button
                    onClick={() => navigate("/restaurants")}
                    className="mt-4 text-sm text-muted-foreground underline"
                >
                    Back to restaurants
                </button>
            </div>
        );
    }
    const grouped = (restaurant.menu_items || []).reduce<Record<string, MenuItem[]>>(
        (acc, item) => {
            const key = item.category?.trim() || "Other";
            (acc[key] = acc[key] || []).push(item);
            return acc;
        },
        {}
    );

    const lower = allergies.map((a) => a.toLowerCase());
    const unsafeCount = (restaurant.menu_items || []).filter((item) =>
        item.allergens.some((a) => lower.includes(a.toLowerCase()))
        ).length;

    return (
        <div className="mx-auto max-w-md px-5 py-8">
        <button
            onClick={() => navigate("/restaurants")}
            className="mb-6 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
            <ArrowLeft className="h-4 w-4" /> Back to map
        </button>

        <h1 className="text-2xl font-semibold tracking-tight">{restaurant.resteraunt_name}</h1>
        <p className="mt-2 flex items-start gap-1.5 text-sm text-muted-foreground">
            <MapPin className="mt-0.5 h-4 w-4 shrink-0" /> {restaurant.location.full_address}
        </p>
        {restaurant.website_url && (
            <p className="mt-1.5 flex items-start gap-1.5 text-sm text-muted-foreground">
            <Globe className="mt-0.5 h-4 w-4 shrink-0" /> {restaurant.website_url}
            </p>
        )}
        {(restaurant.opening_times || []).length > 0 && (
            <div className="mt-1.5">
            {restaurant.opening_times.map((t) => (
                <p key={t} className="flex items-start gap-1.5 text-xs text-muted-foreground">
                <Clock className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {t}
                </p>
            ))}
            </div>
        )}

        {allergies.length === 0 ? (
            <div className="mt-6 rounded-xl border border-border bg-muted/50 p-4 text-sm text-muted-foreground">
            Set your allergies in{" "}
            <Link to="/preferences" className="font-medium text-foreground underline">
                Preferences
            </Link>{" "}
            to highlight items you can't consume.
            </div>
        ) : (
            <div className="mt-6 rounded-xl border border-border bg-muted/50 p-4 text-sm">
            {unsafeCount === 0
                ? "All items look safe for your allergies."
                : `${unsafeCount} of ${(restaurant.menu_items || []).length} items contain your allergens.`}
            </div>
        )}

        {Object.entries(grouped).map(([category, items]) => (
            <section key={category} className="mt-6">
            <h2 className="mb-2 text-sm font-medium text-muted-foreground">{category}</h2>
            <div className="space-y-2">
                {items.map((item, i) => (
                <RestaurantMenuItem key={i} item={item} allergies={allergies} />
                ))}
            </div>
            </section>
        ))}
        </div>
    );
}
