import { ALLER_SCAN_API_BASE_URL, FOOD_FACTS_API_BASE_URL } from "./config";
import { ApiError, get, post } from "./httpClient";

export interface Product {
  id: string;
  barcode: string;
  product_name: string;
  brand?: string;
  allergens: string[];
  source: "external" | "manual";
  createdAt: Date;
}

interface BackendProduct {
  id: string;
  barcode: string;
  product_name: string;
  brand: string | null;
  allergens: string[];
  source: "external" | "manual";
  created_at: Date;
}

interface ExternalProduct {
  brands : string
  product_name_en: string,
  allergens_tags: string[],
  ingredients: any[]
}

interface ExternalRespose {
  code: string,
  product: ExternalProduct
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
    const raw = await get<BackendProduct>(
      `${ALLER_SCAN_API_BASE_URL}/products/get_by_barcode/${encodeURIComponent(barcode)}`
    );
    return mapProduct(raw);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

export async function createProduct(
  barcode: string,
  data: { product_name?: string; brand?: string; allergens?: string[] },
  source: Product["source"] = "external"
): Promise<Product> {
  try {
    const raw = await post<BackendProduct>(`${ALLER_SCAN_API_BASE_URL}/products/`, {
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

export async function lookupProductExternally(barcode: string): Promise<ExternalProduct | null> {
  try {
    const raw = await get<ExternalRespose>(`${FOOD_FACTS_API_BASE_URL}/product/${barcode}.json`, { token: null });

    return raw.product
  }
  catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}
