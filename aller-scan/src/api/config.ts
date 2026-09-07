export const ALLER_SCAN_API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";


export const FOOD_FACTS_API_BASE_URL: string =
  import.meta.env.VITE_FOOD_FACTS_API_BASE_URL ?? "https://world.openfoodfacts.net/api/v3.6";

export const GOOGLE_MAPS_PLACES_API_BASE_URL : string =
  import.meta.env.VITE_GOOGLE_MAPS_PLACES_BASE_URL ?? "https://places.googleapis.com/v1"

export const GOOGLE_MAPS_PLACES_API_KEY : string =
  import.meta.env.VITE_GOOGLE_MAPS_PLACES_API_KEY ?? "YOUR_API_KEY"