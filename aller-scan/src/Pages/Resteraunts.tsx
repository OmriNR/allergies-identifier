import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, Plus, Search, UtensilsCrossed } from "lucide-react";
import {
  Map,
  MapControls,
  MapMarker,
  MarkerContent,
  MarkerTooltip,
  type MapRef,
} from "@/components/ui/map";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { getNearbyResteraunts, type Resteraunt } from "@/api/resteraunts";

const DEFAULT_CENTER: [number, number] = [-74.006, 40.7128];
const INITIAL_SEARCH_RADIUS_METERS = 5000;
const MAX_SEARCH_ATTEMPTS = 10;

export default function Resteraunts() {
  const navigate = useNavigate();
  const mapRef = useRef<MapRef>(null);
  const [center, setCenter] = useState<[number, number] | null>(null);
  const [restaurants, setRestaurants] = useState<Resteraunt[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchNotice, setSearchNotice] = useState("");

  useEffect(() => {
    if (!("geolocation" in navigator)) {
      setCenter(DEFAULT_CENTER);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => setCenter([position.coords.longitude, position.coords.latitude]),
      () => setCenter(DEFAULT_CENTER),
      { timeout: 8000 }
    );
  }, []);

  useEffect(() => {
    if (!center) return;
    let cancelled = false;
    setLoading(true);

    (async () => {
      let found: Resteraunt[] = [];
      try {
        for (let attempt = 0; attempt < MAX_SEARCH_ATTEMPTS; attempt++) {
          const radius = INITIAL_SEARCH_RADIUS_METERS * 2 ** attempt;
          const nearby = await getNearbyResteraunts(center[1], center[0], radius);
          if (cancelled) return;
          if (nearby.length > 0) {
            found = nearby;
            break;
          }
        }
      } finally {
        if (!cancelled) {
          setRestaurants(found);
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [center]);

  const withCoords = restaurants.filter((r) => r.location.coordinates.length === 2);

  const runSearch = () => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return;
    const match = withCoords.find((r) => r.resteraunt_name.toLowerCase().includes(q));
    if (match) {
      mapRef.current?.flyTo({
        center: [match.location.coordinates[0], match.location.coordinates[1]],
        zoom: 16,
      });
      setSearchNotice("");
    } else {
      setSearchNotice(`No restaurant matching "${searchQuery.trim()}" found nearby.`);
    }
  };

  return (
    <div className="relative h-[calc(100dvh-4rem)]">
      {center ? (
        <Map ref={mapRef} center={center} zoom={13} className="h-full w-full">
          <MapControls
            position="top-right"
            showZoom
            showLocate
            showFullscreen
            onLocate={({ longitude, latitude }) => setCenter([longitude, latitude])}
          />
          {withCoords.map((r) => (
            <MapMarker
              key={r.id}
              longitude={r.location.coordinates[0]}
              latitude={r.location.coordinates[1]}
              onClick={() => navigate(`/restaurants/${r.id}`)}
            >
              <MarkerContent className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white bg-primary text-primary-foreground shadow-md">
                <UtensilsCrossed className="h-4 w-4" />
              </MarkerContent>
              <MarkerTooltip>{r.resteraunt_name}</MarkerTooltip>
            </MapMarker>
          ))}
        </Map>
      ) : (
        <div className="flex h-full items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {loading && center && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/60">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {!loading && restaurants.length > 0 && (
        <div className="absolute left-4 right-4 top-4 z-10 flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search restaurants nearby"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runSearch()}
              className="h-10 rounded-xl bg-background/95 pl-9 shadow-md"
            />
          </div>
          <Button onClick={runSearch} className="h-10 shrink-0 rounded-xl shadow-md">
            Go
          </Button>
        </div>
      )}

      {searchNotice && !loading && (
        <Card className="absolute left-4 right-4 top-[68px] z-10 border-0 p-3 text-xs shadow-md">
          {searchNotice}
        </Card>
      )}

      {!loading && restaurants.length === 0 && (
        <Card className="absolute left-4 right-4 top-4 z-10 border-0 p-4 text-center shadow-sm">
          <p className="text-sm font-medium">No restaurants nearby</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Tap the + button to add the first restaurant.
          </p>
        </Card>
      )}

      <button
        onClick={() => navigate("/restaurants/new")}
        className="absolute bottom-5 right-5 z-10 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform active:scale-95"
        aria-label="Add restaurant"
      >
        <Plus className="h-6 w-6" />
      </button>
    </div>
  );
}
