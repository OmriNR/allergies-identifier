import { Plus } from "lucide-react";
import { useState } from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Card } from "../ui/card";
import { COMMON_ALLERGENS } from "@/lib/allergens";
import type { MenuItem } from "@/api/resteraunts";

interface MenuItemFormProps {
    onAdd: (item: MenuItem) => void;
}

export default function MenuItemForm({ onAdd }: MenuItemFormProps) {
    const [name, setName] = useState("");
    const [category, setCategory] = useState("");
    const [ingredients, setIngredients] = useState("");
    const [allergens, setAllergens] = useState<string[]>([]);
    
    const toggleAllergen = (a: string) => 
        setAllergens((prev) => prev.includes(a) ? prev.filter((x) => x !== a) : [...prev, a]);

    const add = () => {
        if (!name.trim()) return;

        onAdd({
            item_name: name.trim(),
            category: category.trim(),
            ingredients: ingredients
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean),
            allergens: allergens
        });

        setName("");
        setCategory("");
        setIngredients("");
        setAllergens([]);
    };

    return (
        <Card className="border-0 p-4 shadow-sm">
            <Input 
                placeholder="Item name (e.g Caesar Salad)"
                value={name}
                onChange={(e) => setName(e.target.value)}
            />

            <Input
                placeholder="Category (e.g. Salads)"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
            />

            <Input
                placeholder="Ingredients, comma separated (e.g. lettuce, parmesan)"
                value={ingredients}
                onChange={(e) => setIngredients(e.target.value)}
            />

            <div>
                <p className="mb-2 text-xs font-medium text-muted-foreground">Allergens</p>
                <div className="flxe flex-wrap gap-1.5">
                    {COMMON_ALLERGENS.map((a) => {
                        const active = allergens.includes(a)
                        return (
                            <button
                                key={a}
                                onClick={() => toggleAllergen(a)}
                                type="button"
                                className={
                                    "rounded-full border px-2.5 py-1 text-xs font-medium transition-colors " +
                                    (active
                                        ? "border-primary bg-primary text-primary-foreground"
                                        : "border-border bg-background text-muted-foreground hover:bg-accent")
                                }
                            >
                                {a}
                            </button>
                        );
                    })}
                </div>
                <Button onClick={add} disabled={!name.trim()} className="w-full">
                    <Plus className="mr-2 h-4 w-4" /> Add item
                </Button>
            </div>
        </Card>
    );
}