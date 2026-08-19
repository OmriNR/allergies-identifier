// Scan results: orchestrates a barcode scan for a user.
//
// - Product already known -> just compare against the user's allergies.
// - Product unknown -> look it up externally, cache it in products.ts,
//   then compare.
// Either way the result is recorded in the user's scan history, linked to
// the product it came from.

import * as products from "./products";
import * as userProperties from "./userProperties";
import { compareAllergens } from "./alerts";
import type { ScanHistoryItem } from "./userProperties";
import type { Product } from "./products";

export interface ScanOutcome {
  historyEntry: ScanHistoryItem;
  product: Product;
}

export async function scanProduct(userId: string, barcode: string): Promise<ScanOutcome> {
  let product = await products.getProductByBarcode(barcode);

  if (!product) {
    const external = await products.lookupProductExternally(barcode);
    product = await products.createProduct(barcode, external);
  }

  const userAllergies = await userProperties.getAllergies(userId);
  const { detected, status } = await compareAllergens(product.allergens, userAllergies);

  const historyEntry = await userProperties.addScanHistoryEntry(userId, {
    productId: product.id,
    barcode: product.barcode,
    product_name: product.product_name,
    brand: product.brand,
    status,
    detected_allergens: detected,
  });

  return { historyEntry, product };
}
