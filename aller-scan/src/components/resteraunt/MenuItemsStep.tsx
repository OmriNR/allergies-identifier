import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, MapPin, Trash2, UtensilsCrossed } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import MenuItemForm from "./MenuItemForm";
import { createResteraunt, type MenuItem, type Resteraunt } from "@/api/resteraunts";

interface MenuItemsStepProps {
    place: Resteraunt
}

export default function MenuItemsStep({ place }: MenuItemsStepProps) {
    const navigate = useNavigate();
    const [items, setItems] = useState<MenuItem[]>([]);
    const [saving, setSaving] = useState(false);

    const addItem = (item: MenuItem) => setItems((prev) => [...prev, item])

    const removeItem = (index: number) => setItems((prev) => prev.filter((_, i) => i !== index));

    const save = async () => {
        setSaving(true);

        try {
            await createResteraunt({
                id: place.id,
                added_by: place.added_by,
                resteraunt_name: place.resteraunt_name,
                location: {
                    full_address: place.location.full_address,
                    coordinates: place.location.coordinates,
                },
                opening_times: place.opening_times,
                website_url: place.website_url,
                menu_items: items
            });

            toast.success("Resteraunt added");
            navigate("/resteraunts");
        } catch {
            toast.error("Could not add resteraunt");
        } finally {
            setSaving(false)
        }
    }

    return (
        <div>
            <Card className="mt-6 border-0 p-4 shadow-sm">
                <p className="text-sm font-semibold">{place.resteraunt_name}</p>
                <p className="mt-1 flex items-start gap-1.5 text-xs text-muted-foreground">
                    <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {place.location.full_address}
                </p>
            </Card>

            <h2 className="mt-8 flex items-center gap-2 text-base font-semibold">
                <UtensilsCrossed className="h-4 w-4" /> Menu items
            </h2>
            <p className="mt-1 text-xs text-muted-foreground">
                Add each dish with its ingredients and allergens so others get safety alerts.
            </p>

            <div className="mt-4">
                <MenuItemForm onAdd={addItem}/>
            </div>

             {items.length > 0 && (
                <div className="mt-4 space-y-2">
                    {items.map((item, index) => (
                        <div
                            key={index}
                            className="flex items-start justify-between gap-3 rounded-xl border border-border bg-card p-3.5"
                        >
                            <div className="min-w-0">
                                <p className="text-sm font-medium">{item.item_name}</p>
                                <p className="text-xs text-muted-foreground">
                                {item.category || "Uncategorized"}
                                </p>
                                {item.allergens.length > 0 && (
                                <p className="mt-1 text-xs text-red-600">{item.allergens.join(", ")}</p>
                                )}
                            </div>
                            <button
                                onClick={() => removeItem(index)}
                                className="shrink-0 text-muted-foreground hover:text-destructive"
                                aria-label="Remove item"
                            >
                                <Trash2 className="h-4 w-4" />
                            </button>
                        </div>
                    ))}
                </div>
            )}

            <Button onClick={save} disabled={saving || items.length === 0} className="mt-6 w-full">
                {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Save resteraunt
            </Button>
        </div>
    );
}