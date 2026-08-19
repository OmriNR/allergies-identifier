// Alerts: compare a product's known allergens against a user's allergies.
// Product lookup/caching lives in products.ts; scans.ts orchestrates the two.

import { delay } from "./_mockClient";

export interface AllergenCheckResult {
  detected: string[];
  status: "safe" | "dangerous";
}

export async function compareAllergens(
  productAllergens: string[],
  userAllergies: string[]
): Promise<AllergenCheckResult> {
  const detected = productAllergens.filter((allergen) =>
    userAllergies.some((u) => u.toLowerCase() === allergen.toLowerCase())
  );

  return delay({
    detected,
    status: detected.length > 0 ? "dangerous" : "safe",
  });
}
