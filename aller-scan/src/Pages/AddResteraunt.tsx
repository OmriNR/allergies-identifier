import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import RestaurantSearchStep from "@/components/resteraunt/ResterauntSearchStep";
import MenuItemsStep from "@/components/resteraunt/MenuItemsStep";
import type { Resteraunt } from "@/api/resteraunts";

export default function AddResteraunt() {
    const navigate = useNavigate();
    const [place, setPlace] = useState<Resteraunt | null>(null);

    return (
        <div className="mx-auto max-w-md px-5 py-8">
            <button 
                onClick={() => (place ? setPlace(null) : navigate("/restaurants"))}
                className="mb-6 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
            >
                    <ArrowLeft className="h-4 w-4"/> Back
            </button>

            <h1 className="text-2xl font-semibold tracking-tight">Add restaurant</h1>
            <p className="mt-1 text-sm text-muted-foreground">
                {place
                    ? `Step 2 of 2 - add menu items for ${place.resteraunt_name}`
                    : "Step 1 of 2 - find the resteraunt on Google Maps"}
            </p>

            {place ? (
                <MenuItemsStep place={place} />
            ) : (
                <RestaurantSearchStep onFound={setPlace} />
            )}
        </div>
    )
}