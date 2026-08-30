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
    product = await products.createProduct(barcode, {
      product_name: external?.product_name_en,
      brand: external?.brands,
      allergens: external?.allergens_tags.map(allergan => allergan.replace(/^en:/, ""))
    });
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
