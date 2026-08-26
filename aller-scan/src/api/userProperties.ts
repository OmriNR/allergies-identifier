// Per-user data: allergy preferences and scan history.

import { delay, generateId, readCollection, writeCollection } from "./_mockClient";

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

interface AllergyPreference {
  userId: string;
  allergies: string[];
  updatedAt: string;
}

const scanHistorySeed: ScanHistoryItem[] = [
  {
    id: "seed-1",
    userId: "seed-user-1",
    productId: "seed-product-1",
    barcode: "5901234123457",
    product_name: "Crunchy Peanut Butter",
    brand: "NutCo",
    status: "dangerous",
    detected_allergens: ["Peanuts"],
    created_date: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
  },
  {
    id: "seed-2",
    userId: "seed-user-1",
    productId: "seed-product-2",
    barcode: "7290000066318",
    product_name: "Oat Milk",
    brand: "GreenFarm",
    status: "safe",
    detected_allergens: [],
    created_date: new Date(Date.now() - 1000 * 60 * 60 * 26).toISOString(),
  },
  {
    id: "seed-3",
    userId: "seed-user-1",
    productId: "seed-product-3",
    barcode: "0850027870016",
    product_name: "Whole Wheat Crackers",
    brand: "Baker's Choice",
    status: "dangerous",
    detected_allergens: ["Gluten", "Soybeans"],
    created_date: new Date(Date.now() - 1000 * 60 * 60 * 50).toISOString(),
  },
];

const allergyPreferencesSeed: AllergyPreference[] = [
  { userId: "seed-user-1", allergies: ["Peanuts", "Gluten"], updatedAt: new Date().toISOString() },
];

function scanHistory(): ScanHistoryItem[] {
  return readCollection<ScanHistoryItem>("scanHistory", scanHistorySeed);
}

function allergyPreferences(): AllergyPreference[] {
  return readCollection<AllergyPreference>("allergyPreferences", allergyPreferencesSeed);
}

export async function getAllergies(userId: string): Promise<string[]> {
  const pref = allergyPreferences().find((p) => p.userId === userId);
  return delay(pref?.allergies ?? []);
}

export async function updateAllergies(userId: string, allergies: string[]): Promise<string[]> {
  const all = allergyPreferences();
  const index = all.findIndex((p) => p.userId === userId);
  const updatedAt = new Date().toISOString();

  if (index === -1) {
    writeCollection("allergyPreferences", [...all, { userId, allergies, updatedAt }]);
  } else {
    const next = [...all];
    next[index] = { userId, allergies, updatedAt };
    writeCollection("allergyPreferences", next);
  }

  return delay(allergies);
}

export async function getScanHistory(userId: string, limit?: number): Promise<ScanHistoryItem[]> {
  const items = scanHistory()
    .filter((item) => item.userId === userId)
    .sort((a, b) => (a.created_date < b.created_date ? 1 : -1));
  return delay(typeof limit === "number" ? items.slice(0, limit) : items);
}

export async function addScanHistoryEntry(
  userId: string,
  entry: Omit<ScanHistoryItem, "id" | "userId" | "created_date">
): Promise<ScanHistoryItem> {
  const record: ScanHistoryItem = {
    ...entry,
    id: generateId(),
    userId,
    created_date: new Date().toISOString(),
  };
  writeCollection("scanHistory", [record, ...scanHistory()]);
  return delay(record);
}
