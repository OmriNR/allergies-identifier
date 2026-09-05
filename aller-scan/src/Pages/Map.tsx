import { useEffect, useState } from "react";
import { Map, MapControls } from "@/components/ui/map";
import { Card } from "@/components/ui/card";

const DEFAULT_CENTER: [number, number] = [-74.006, 40.7128];

export default function ResterauntsMap() {
  const [center, setCenter] = useState<[number, number] | null>(null);

  useEffect(() => {
    if (!("geolocation" in navigator)) {
      setCenter(DEFAULT_CENTER);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => setCenter([position.coords.longitude, position.coords.latitude]),
      () => setCenter(DEFAULT_CENTER),
    );
  }, []);

  return (
    <Card className="h-full rounded-none p-0 overflow-hidden">
      {center ? (
        <Map center={center} zoom={13}>
          <MapControls
            position="top-right"
            showZoom
            showLocate
            showFullscreen
          />
        </Map>
      ) : (
        <div className="flex h-full items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-800" />
        </div>
      )}
    </Card>
  )
}