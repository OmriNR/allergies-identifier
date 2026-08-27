// Per-user data: allergy preferences and scan history. Backed by
// /user-properties on the aller-scan-api.

import { ApiError, apiRequest } from "./httpClient";

export interface ScanHistoryItem {
  id: string;
  userId: string;
  productId: string;
  barcode: string;
  // Snapshot of the product/result as they were at scan time, so history
  // stays accurate even if the shared product record changes later.
  product_name: string;
  brand?: string;
  status: "safe" | "dangerous";
  detected_allergens?: string[];
  created_date: string;
}

interface BackendScanHistory {
  id: string;
  user_id: string;
  product_id: string;
  barcode: string;
  product_name: string;
  brand: string | null;
  status: "safe" | "dangerous";
  detected_allergens: string[];
  created_at: string;
}

interface BackendAllergyPreference {
  user_id: string;
  allergies: string[];
  updated_at: string;
}

function mapScanHistory(raw: BackendScanHistory): ScanHistoryItem {
  return {
    id: raw.id,
    userId: raw.user_id,
    productId: raw.product_id,
    barcode: raw.barcode,
    product_name: raw.product_name,
    brand: raw.brand ?? undefined,
    status: raw.status,
    detected_allergens: raw.detected_allergens,
    created_date: raw.created_at,
  };
}

export async function getAllergies(userId: string): Promise<string[]> {
  try {
    const raw = await apiRequest<BackendAllergyPreference>(`/user-properties/allergies/${userId}`);
    return raw.allergies;
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return [];
    throw err;
  }
}

// The backend has separate create (POST, 404 if no such user, 400 if a
// preference already exists) and update (PUT, 404 if none exists yet)
// endpoints; try update first and fall back to create the first time.
export async function updateAllergies(userId: string, allergies: string[]): Promise<string[]> {
  try {
    const raw = await apiRequest<BackendAllergyPreference>(`/user-properties/allergies/${userId}`, {
      method: "PUT",
      json: { userid: userId, allergies },
    });
    return raw.allergies;
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      const raw = await apiRequest<BackendAllergyPreference>("/user-properties/allergies", {
        method: "POST",
        json: { user_id: userId, allergies },
      });
      return raw.allergies;
    }
    throw err;
  }
}

// The backend returns the user's full history with no pagination; sort
// newest-first and slice client-side to honor `limit`.
export async function getScanHistory(userId: string, limit?: number): Promise<ScanHistoryItem[]> {
  const raw = await apiRequest<BackendScanHistory[]>(`/user-properties/scan-history/users/${userId}`);
  const items = raw.map(mapScanHistory).sort((a, b) => (a.created_date < b.created_date ? 1 : -1));
  return typeof limit === "number" ? items.slice(0, limit) : items;
}

export async function addScanHistoryEntry(
  userId: string,
  entry: Omit<ScanHistoryItem, "id" | "userId" | "created_date">
): Promise<ScanHistoryItem> {
  const raw = await apiRequest<BackendScanHistory>("/user-properties/scan-history", {
    method: "POST",
    json: {
      user_id: userId,
      product_id: entry.productId,
      barcode: entry.barcode,
      product_name: entry.product_name,
      brand: entry.brand,
      status: entry.status,
      detected_allergens: entry.detected_allergens ?? [],
    },
  });
  return mapScanHistory(raw);
}
