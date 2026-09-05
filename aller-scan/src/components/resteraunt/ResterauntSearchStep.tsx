import { useState } from "react";
import { ArrowRight, Clock, Globe, Loader2, MapPin, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { searchGoogleMapsPlace } from "@/lib/placeSearch";
import type { Resteraunt } from "@/api/resteraunts";

interface RestaurantSearchStepProps {
  onFound: (place: Resteraunt) => void;
}

export default function RestaurantSearchStep({ onFound }: RestaurantSearchStepProps) {
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Resteraunt | null>(null);

  const search = async () => {
    if (!query.trim()) return;
    setSearching(true);
    setError("");
    setResult(null);
    try {
      const place = await searchGoogleMapsPlace(query.trim());
      if (!place.found) {
        setError("No matching place found on Google Maps. Try the full name and add the city.");
        return;
      }
      setResult(place);
    } catch (err) {
      const detail = (err as { response?: { data?: { error?: string } } })?.response
        ?.data?.error;
      setError(detail || "Something went wrong while searching. Please try again.");
    } finally {
      setSearching(false);
    }
  };

  return (
    <div>
      <div className="mt-6 flex gap-2">
        <Input
          placeholder="Restaurant name (e.g. Pizza Roma, Berlin)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
        />
        <Button onClick={search} disabled={searching || !query.trim()}>
          {searching ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Search className="h-4 w-4" />
          )}
        </Button>
      </div>

      {error && (
        <p className="mt-3 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</p>
      )}

      {result && (
        <Card className="mt-4 border-0 p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Found on Google Maps
          </p>
          <p className="mt-1 text-base font-semibold">{result.resteraunt_name}</p>
          <p className="mt-2 flex items-start gap-1.5 text-xs text-muted-foreground">
            <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {result.location.full_address}
          </p>
          {result.website_url && (
            <p className="mt-1.5 flex items-start gap-1.5 text-xs text-muted-foreground">
              <Globe className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {result.website_url}
            </p>
          )}
          {result.opening_times.length > 0 && (
            <div className="mt-1.5">
              {result.opening_times.map((t) => (
                <p key={t} className="flex items-start gap-1.5 text-xs text-muted-foreground">
                  <Clock className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {t}
                </p>
              ))}
            </div>
          )}
          <Button onClick={() => onFound(result)} className="mt-4 w-full">
            Continue to menu <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </Card>
      )}
    </div>
  );
}