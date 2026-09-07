import { GOOGLE_MAPS_PLACES_API_KEY, GOOGLE_MAPS_PLACES_API_BASE_URL } from "./config";
import { ApiError, post } from "./httpClient";

export interface GooglePlace {
    id: string
    displayName: string
    formattedAddress: string
    location: GooglePlaceLocation
    websiteUri: string
    weekdayDescriptions: string[]
}

export interface GooglePlaceLocation {
    latitude: number
    longitude: number
}

interface RawGooglePlace {
    id: string
    displayName?: { text: string; languageCode?: string }
    formattedAddress?: string
    location?: GooglePlaceLocation
    websiteUri?: string
    regularOpeningHours?: { weekdayDescriptions?: string[] }
}

interface SearchTextResponse {
    places?: RawGooglePlace[]
}

const FIELD_MASK = [
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.websiteUri",
    "places.regularOpeningHours.weekdayDescriptions",
].join(",");

function toGooglePlace(raw: RawGooglePlace): GooglePlace {
    return {
        id: raw.id,
        displayName: raw.displayName?.text ?? "",
        formattedAddress: raw.formattedAddress ?? "",
        location: raw.location ?? { latitude: 0, longitude: 0 },
        websiteUri: raw.websiteUri ?? "",
        weekdayDescriptions: raw.regularOpeningHours?.weekdayDescriptions ?? [],
    };
}

export async function searchWithGoogle(placeName: string): Promise<GooglePlace[] | null> {
    try {
        const response = await post<SearchTextResponse>(
            `${GOOGLE_MAPS_PLACES_API_BASE_URL}/places:searchText`,
            {
                json: { textQuery: placeName },
                token: null,
                headers: {
                    "X-Goog-Api-Key": GOOGLE_MAPS_PLACES_API_KEY,
                    "X-Goog-FieldMask": FIELD_MASK,
                },
            }
        );

        return (response.places ?? []).map(toGooglePlace);
    } catch (error) {
        if (error instanceof ApiError) {
            return null;
        }
        throw error;
    }
}
