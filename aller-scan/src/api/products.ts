// Products: a shared cache of barcode -> product/allergen data, built up as
// users scan things. Independent of any one user. Backed by /products on
// the aller-scan-api.

import { ApiError, apiRequest } from "./httpClient";

export interface Product {
  id: string;
  barcode: string;
  product_name: string;
  brand?: string;
  allergens: string[];
  source: "external" | "manual";
  createdAt: string;
}

interface BackendProduct {
  id: string;
  barcode: string;
  product_name: string;
  brand: string | null;
  allergens: string[];
  source: "external" | "manual";
  created_at: string;
}

function mapProduct(raw: BackendProduct): Product {
  return {
    id: raw.id,
    barcode: raw.barcode,
    product_name: raw.product_name,
    brand: raw.brand ?? undefined,
    allergens: raw.allergens,
    source: raw.source,
    createdAt: raw.created_at,
  };
}

export async function getProductByBarcode(barcode: string): Promise<Product | null> {
  try {
    const raw = await apiRequest<BackendProduct>(`/products/get_by_barcode/${encodeURIComponent(barcode)}`);
    return mapProduct(raw);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

// Barcode is treated as a unique key server-side: if a concurrent caller
// already created this product (e.g. a double-invoked effect, two tabs
// scanning the same new barcode at once), reuse it instead of erroring.
export async function createProduct(
  barcode: string,
  data: { product_name: string; brand?: string; allergens: string[] },
  source: Product["source"] = "external"
): Promise<Product> {
  try {
    const raw = await apiRequest<BackendProduct>("/products/", {
      method: "POST",
      json: {
        barcode,
        product_name: data.product_name,
        brand: data.brand,
        allergens: data.allergens,
        source,
      },
    });
    return mapProduct(raw);
  } catch (err) {
    if (err instanceof ApiError && (err.status === 400 || err.status === 409)) {
      const existing = await getProductByBarcode(barcode);
      if (existing) return existing;
    }
    throw err;
  }
}

const fallbackAllergenPool = [
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
];

function hashString(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i++) {
    hash = (hash << 5) - hash + value.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

function delay<T>(value: T, ms = 300): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

// Placeholder for the real external product/allergen lookup (nutrition
// database, barcode API, LLM, etc.) — provider is still being researched
// and isn't part of aller-scan-api. Swap this implementation out once one
// is chosen; callers only depend on the { product_name, brand, allergens }
// shape below.
export async function lookupProductExternally(
  barcode: string
): Promise<{ product_name: string; brand: string; allergens: string[] }> {
  const hash = hashString(barcode);
  const allergenCount = hash % 3;
  const allergens = new Set(
    Array.from(
      { length: allergenCount },
      (_, i) => fallbackAllergenPool[(hash + i * 7) % fallbackAllergenPool.length]
    )
  );

  return delay(
    {
      product_name: `Mock Product ${barcode.slice(-4)}`,
      brand: "Sample Brand",
      allergens: [...allergens],
    },
    600
  );
}
