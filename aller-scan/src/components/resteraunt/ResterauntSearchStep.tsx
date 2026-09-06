import { useState } from "react";
import { ArrowRight, Clock, Globe, Loader2, MapPin, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { searchWithGoogle, type GooglePlace } from "@/api/googleSearch";
import type { Resteraunt } from "@/api/resteraunts";

interface RestaurantSearchStepProps {
  onFound: (place: Resteraunt) => void;
}

function toResteraunt(place: GooglePlace): Resteraunt {
  return {
    id: place.id,
    resteraunt_name: place.displayName,
    added_by: "",
    opening_times: place.weekdayDescriptions,
    location: {
      full_address: place.formattedAddress,
      coordinates: [place.location.longitude, place.location.latitude],
    },
    website_url: place.websiteUri || undefined,
    menu_items: [],
    properties: {},
  };
}

export default function RestaurantSearchStep({ onFound }: RestaurantSearchStepProps) {
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");
  const [results, setResults] = useState<GooglePlace[]>([]);
  const [selected, setSelected] = useState<GooglePlace | null>(null);

  const search = async () => {
    if (!query.trim()) return;
    setSearching(true);
    setError("");
    setResults([]);
    setSelected(null);
    try {
      const places = await searchWithGoogle(query.trim());
      if (!places || places.length === 0) {
        setError("No matching place found on Google Maps. Try the full name and add the city.");
        return;
      }
      setResults(places);
    } catch {
      setError("Something went wrong while searching. Please try again.");
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

      {results.length > 0 && !selected && (
        <div className="mt-4 flex flex-col gap-2">
          {results.map((place) => (
            <button
              key={place.id}
              type="button"
              onClick={() => setSelected(place)}
              className="rounded-lg border border-border bg-card p-3 text-left text-sm transition-colors hover:bg-muted"
            >
              <p className="font-medium">{place.displayName}</p>
              <p className="mt-0.5 flex items-start gap-1.5 text-xs text-muted-foreground">
                <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {place.formattedAddress}
              </p>
            </button>
          ))}
        </div>
      )}

      {selected && (
        <Card className="mt-4 border-0 p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Found on Google Maps
          </p>
          <p className="mt-1 text-base font-semibold">{selected.displayName}</p>
          <p className="mt-2 flex items-start gap-1.5 text-xs text-muted-foreground">
            <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {selected.formattedAddress}
          </p>
          {selected.websiteUri && (
            <p className="mt-1.5 flex items-start gap-1.5 text-xs text-muted-foreground">
              <Globe className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {selected.websiteUri}
            </p>
          )}
          {selected.weekdayDescriptions.length > 0 && (
            <div className="mt-1.5">
              {selected.weekdayDescriptions.map((t) => (
                <p key={t} className="flex items-start gap-1.5 text-xs text-muted-foreground">
                  <Clock className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {t}
                </p>
              ))}
            </div>
          )}
          <div className="mt-4 flex gap-2">
            <Button variant="outline" onClick={() => setSelected(null)} className="flex-1">
              Back to results
            </Button>
            <Button onClick={() => onFound(toResteraunt(selected))} className="flex-1">
              Continue to menu <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
