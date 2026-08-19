import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Check, Loader2 } from "lucide-react";
import * as userPropertiesApi from "@/api/userProperties";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import { useAuth } from "@/lib/AuthContext";

const COMMON_ALLERGENS: string[] = [
  "Milk",
  "Eggs",
  "Fish",
  "Shellfish",
  "Tree nuts",
  "Peanuts",
  "Wheat",
  "Soybeans",
  "Gluten",
  "Sesame",
  "Sulfites",
  "Mustard",
  "Celery",
  "Lupin",
];

export default function Preferences() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }
    userPropertiesApi
      .getAllergies(user.id)
      .then((allergies) => setSelected(allergies))
      .finally(() => setLoading(false));
  }, [user]);

  const toggle = (allergen: string) => {
    setSelected((prev) =>
      prev.includes(allergen) ? prev.filter((a) => a !== allergen) : [...prev, allergen]
    );
  };

  const save = async () => {
    if (!user) return;
    setSaving(true);
    try {
      await userPropertiesApi.updateAllergies(user.id, selected);
      toast.success("Allergies saved");
      navigate("/");
    } catch {
      toast.error("Could not save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-md px-5 py-8">
      <button
        onClick={() => navigate("/")}
        className="mb-6 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> Back
      </button>

      <h1 className="text-2xl font-semibold tracking-tight">My allergies</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Select the allergens you want to be alerted about when scanning products.
      </p>

      <Card className="mt-6 border-0 p-5 shadow-sm">
        {loading ? (
          <div className="flex justify-center py-10">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-2">
            {COMMON_ALLERGENS.map((allergen) => {
              const active = selected.includes(allergen);
              return (
                <button
                  key={allergen}
                  onClick={() => toggle(allergen)}
                  className={
                    "flex items-center justify-between rounded-xl border px-3.5 py-3 text-sm font-medium transition-colors " +
                    (active
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border bg-background hover:bg-accent")
                  }
                >
                  {allergen}
                  {active && <Check className="h-4 w-4" />}
                </button>
              );
            })}
          </div>
        )}
      </Card>

      <Button onClick={save} disabled={saving || loading} className="mt-6 w-full">
        {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
        Save preferences
      </Button>
    </div>
  );
}