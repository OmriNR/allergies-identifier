// Products: a shared cache of barcode -> product/allergen data, built up as
// users scan things. Independent of any one user.

import { delay, generateId, readCollection, writeCollection } from "./_mockClient";

export interface Product {
  id: string;
  barcode: string;
  product_name: string;
  brand?: string;
  allergens: string[];
  source: "external" | "manual";
  createdAt: string;
}

const productsSeed: Product[] = [
  {
    id: "seed-product-1",
    barcode: "5901234123457",
    product_name: "Crunchy Peanut Butter",
    brand: "NutCo",
    allergens: ["Peanuts"],
    source: "manual",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
  },
  {
    id: "seed-product-2",
    barcode: "7290000066318",
    product_name: "Oat Milk",
    brand: "GreenFarm",
    allergens: [],
    source: "manual",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 26).toISOString(),
  },
  {
    id: "seed-product-3",
    barcode: "0850027870016",
    product_name: "Whole Wheat Crackers",
    brand: "Baker's Choice",
    allergens: ["Gluten", "Soybeans"],
    source: "manual",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 50).toISOString(),
  },
];

function products(): Product[] {
  return readCollection<Product>("products", productsSeed);
}

export async function getProductByBarcode(barcode: string): Promise<Product | null> {
  const product = products().find((p) => p.barcode === barcode);
  return delay(product ?? null);
}

// Barcode is treated as a unique key: if a concurrent caller already
// created this product (e.g. a double-invoked effect, two tabs scanning
// the same new barcode at once), reuse it instead of creating a duplicate.
export async function createProduct(
  barcode: string,
  data: { product_name: string; brand?: string; allergens: string[] },
  source: Product["source"] = "external"
): Promise<Product> {
  const existing = products().find((p) => p.barcode === barcode);
  if (existing) {
    return delay(existing);
  }

  const record: Product = {
    id: generateId(),
    barcode,
    product_name: data.product_name,
    brand: data.brand,
    allergens: data.allergens,
    source,
    createdAt: new Date().toISOString(),
  };
  writeCollection("products", [record, ...products()]);
  return delay(record);
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

// Placeholder for the real external product/allergen lookup (nutrition
// database, barcode API, LLM, etc.) — provider is still being researched.
// Swap this implementation out once one is chosen; callers only depend on
// the { product_name, brand, allergens } shape below.
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
