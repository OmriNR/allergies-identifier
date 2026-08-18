// Mock stand-in for the base44 SDK client.
// Mirrors the bits of the real base44 shape this app touches
// (base44.entities.<Entity>.list/create/update/remove) so it can be swapped
// back out for the real client later without touching call sites.

const STORAGE_PREFIX = "mock-base44:";

function readCollection<T>(name: string, seed: T[]): T[] {
  const raw = localStorage.getItem(STORAGE_PREFIX + name);
  if (!raw) {
    localStorage.setItem(STORAGE_PREFIX + name, JSON.stringify(seed));
    return seed;
  }
  try {
    return JSON.parse(raw) as T[];
  } catch {
    return seed;
  }
}

function writeCollection<T>(name: string, items: T[]) {
  localStorage.setItem(STORAGE_PREFIX + name, JSON.stringify(items));
}

function delay<T>(value: T, ms = 300): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

interface WithId {
  id: string;
  created_date?: string;
}

function createEntityClient<T extends WithId>(name: string, seed: T[]) {
  return {
    async list(sort?: string, limit?: number): Promise<T[]> {
      const items = [...readCollection<T>(name, seed)];

      if (sort) {
        const desc = sort.startsWith("-");
        const key = (desc ? sort.slice(1) : sort) as keyof T;
        items.sort((a, b) => {
          const av = a[key];
          const bv = b[key];
          if (av === bv) return 0;
          const cmp = av > bv ? 1 : -1;
          return desc ? -cmp : cmp;
        });
      }

      return delay(typeof limit === "number" ? items.slice(0, limit) : items);
    },

    async filter(predicate: Partial<T>): Promise<T[]> {
      const items = readCollection<T>(name, seed);
      const matches = items.filter((item) =>
        Object.entries(predicate).every(([key, value]) => item[key as keyof T] === value)
      );
      return delay(matches);
    },

    async get(id: string): Promise<T | undefined> {
      const items = readCollection<T>(name, seed);
      return delay(items.find((item) => item.id === id));
    },

    async create(data: Omit<T, "id" | "created_date">): Promise<T> {
      const items = readCollection<T>(name, seed);
      const record = {
        ...data,
        id: crypto.randomUUID(),
        created_date: new Date().toISOString(),
      } as T;
      writeCollection(name, [record, ...items]);
      return delay(record);
    },

    async update(id: string, data: Partial<T>): Promise<T | undefined> {
      const items = readCollection<T>(name, seed);
      let updated: T | undefined;
      const next = items.map((item) => {
        if (item.id === id) {
          updated = { ...item, ...data };
          return updated;
        }
        return item;
      });
      writeCollection(name, next);
      return delay(updated);
    },

    async remove(id: string): Promise<void> {
      const items = readCollection<T>(name, seed);
      writeCollection(
        name,
        items.filter((item) => item.id !== id)
      );
      return delay(undefined);
    },
  };
}

interface ScanHistoryRecord extends WithId {
  barcode: string;
  product_name: string;
  brand?: string;
  status: "safe" | "dangerous";
  detected_allergens?: string[];
  created_date: string;
}

const scanHistorySeed: ScanHistoryRecord[] = [
  {
    id: "seed-1",
    barcode: "5901234123457",
    product_name: "Crunchy Peanut Butter",
    brand: "NutCo",
    status: "dangerous",
    detected_allergens: ["peanuts"],
    created_date: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
  },
  {
    id: "seed-2",
    barcode: "7290000066318",
    product_name: "Oat Milk",
    brand: "GreenFarm",
    status: "safe",
    detected_allergens: [],
    created_date: new Date(Date.now() - 1000 * 60 * 60 * 26).toISOString(),
  },
  {
    id: "seed-3",
    barcode: "0850027870016",
    product_name: "Whole Wheat Crackers",
    brand: "Baker's Choice",
    status: "dangerous",
    detected_allergens: ["gluten", "soy"],
    created_date: new Date(Date.now() - 1000 * 60 * 60 * 50).toISOString(),
  },
];

interface UserPreferenceRecord extends WithId {
  allergies: string[];
  created_date: string;
}

const userPreferenceSeed: UserPreferenceRecord[] = [
  {
    id: "seed-1",
    allergies: ["Peanuts", "Gluten"],
    created_date: new Date().toISOString(),
  },
];

interface InvokeLLMParams {
  prompt: string;
  add_context_from_internet?: boolean;
  response_json_schema?: Record<string, unknown>;
}

interface MockProduct {
  product_name: string;
  brand: string;
  allergens: string[];
}

const mockProductCatalog: Record<string, MockProduct> = {
  "5901234123457": { product_name: "Crunchy Peanut Butter", brand: "NutCo", allergens: ["Peanuts"] },
  "7290000066318": { product_name: "Oat Milk", brand: "GreenFarm", allergens: [] },
  "0850027870016": {
    product_name: "Whole Wheat Crackers",
    brand: "Baker's Choice",
    allergens: ["Gluten", "Soybeans"],
  },
};

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

function mockProductForBarcode(barcode: string): MockProduct {
  if (mockProductCatalog[barcode]) return mockProductCatalog[barcode];

  const hash = hashString(barcode);
  const allergenCount = hash % 3;
  const allergens = new Set(
    Array.from(
      { length: allergenCount },
      (_, i) => fallbackAllergenPool[(hash + i * 7) % fallbackAllergenPool.length]
    )
  );

  return {
    product_name: `Mock Product ${barcode.slice(-4)}`,
    brand: "Sample Brand",
    allergens: [...allergens],
  };
}

export const base44 = {
  entities: {
    ScanHistory: createEntityClient<ScanHistoryRecord>("ScanHistory", scanHistorySeed),
    UserPreference: createEntityClient<UserPreferenceRecord>("UserPreference", userPreferenceSeed),
  },
  integrations: {
    Core: {
      async InvokeLLM(params: InvokeLLMParams): Promise<MockProduct> {
        const barcode = params.prompt.match(/barcode "([^"]+)"/)?.[1] ?? "unknown";
        return delay(mockProductForBarcode(barcode), 600);
      },
    },
  },
};
