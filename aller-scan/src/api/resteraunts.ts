import { ALLER_SCAN_API_BASE_URL } from "./config";
import { ApiError, get, put, post, del } from "./httpClient";

export interface Resteraunt {
    id: string
    resteraunt_name: string,
    added_by: string
    opening_times: string[],
    location: Location
    website_url?: string
    menu_items: MenuItem[]
    properties: Record<string, boolean>
}

export interface Location {
    full_address: string
    coordinates: number[]
}

export interface MenuItem {
    item_name: string
    category: string
    ingredients: string[]
    allergens: string[]
}

export interface ResterauntCreateInput {
    id: string
    added_by: string
    resteraunt_name: string
    opening_times: string[]
    location: Location
    menu_items: MenuItem[]
    website_url?: string
    properties?: Record<string, boolean>
}

export interface ResterauntUpdateInput {
    opening_times: string[]
    menu_items: MenuItem[]
    website_url?: string
    properties?: Record<string, boolean>
}

export async function getResteraunt(id: string): Promise<Resteraunt | null> {
    try {
        const resteraunt = await get<Resteraunt>(`${ALLER_SCAN_API_BASE_URL}/resteraunts/${id}`);
        return resteraunt;
    } catch (err) {
        if (err instanceof ApiError && err.status === 404) return null;
        throw err;
    }
}

export async function createResteraunt(data: ResterauntCreateInput): Promise<Resteraunt> {
    return post<Resteraunt>(`${ALLER_SCAN_API_BASE_URL}/resteraunts/`, { json: data });
}

export async function updateResteraunt(id: string, data: ResterauntUpdateInput): Promise<Resteraunt> {
    return put<Resteraunt>(`${ALLER_SCAN_API_BASE_URL}/resteraunts/${id}`, { json: data });
}

export async function deleteResteraunt(id: string): Promise<Resteraunt> {
    return del<Resteraunt>(`${ALLER_SCAN_API_BASE_URL}/resteraunts/${id}`);
}

export async function getNearbyResteraunts(
    latitude: number,
    longitude: number,
    radiusMeters?: number
): Promise<Resteraunt[]> {
    try {
        return await get<Resteraunt[]>(`${ALLER_SCAN_API_BASE_URL}/resteraunts/nearby`, {
            query: { latitude, longitude, radius_meters: radiusMeters },
        });
    } catch (err) {
        if (err instanceof ApiError && err.status === 404) return [];
        throw err;
    }
}

