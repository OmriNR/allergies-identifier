// Seeds the aller-scan Mongo database with sample products, restaurants and a
// master user, so the app has something to look at besides an empty state.
//
// Run against the running `mongo` container (see scripts/seed_mock_data.md
// for the exact docker compose commands). Safe to re-run: every write is an
// upsert keyed on a natural/stable id, so re-running just refreshes the data
// instead of creating duplicates.

// --- indexes (defensive: normally created by the API on startup via Beanie) ---
db.users.createIndex({ uuid: 1 }, { unique: true });
db.users.createIndex({ email: 1 }, { unique: true });
db.products.createIndex({ barcode: 1 }, { unique: true });
db.resteraunts.createIndex({ "location.coordinates": "2dsphere" });

// --- master user (no allergy preferences, no scan history) ---
const masterUserUuid = UUID();

db.users.updateOne(
  { email: "master@allerscan.dev" },
  {
    $setOnInsert: {
      uuid: masterUserUuid,
      created_at: new Date(),
    },
    $set: {
      name: "Master User",
      // bcrypt hash of "Master123!", generated with the same passlib/bcrypt
      // setup app/auth/auth.py uses, so login works as-is.
      password: "$2b$12$nWKntJQdpONzHpkgy72Zb.EokwuWcujynuQJKRbkoBEzM7xOE6yZq",
      avatar_url: null,
      is_active: true,
      is_superuser: false,
    },
  },
  { upsert: true }
);

const masterUser = db.users.findOne({ email: "master@allerscan.dev" });
const masterUserId = masterUser.uuid;

// --- products ---
const products = [
  {
    barcode: "0049000028911",
    product_name: "Original Peanut Butter",
    brand: "Skippy",
    allergens: ["peanuts"],
    source: "external",
  },
  {
    barcode: "0038000138416",
    product_name: "Honey Nut Cheerios",
    brand: "General Mills",
    allergens: ["gluten", "tree nuts"],
    source: "external",
  },
  {
    barcode: "0016000275867",
    product_name: "Chocolate Chip Cookies",
    brand: "Betty Crocker",
    allergens: ["gluten", "dairy", "egg", "soy"],
    source: "manual",
  },
  {
    barcode: "0041220576453",
    product_name: "Unsweetened Almond Milk",
    brand: "Silk",
    allergens: ["tree nuts"],
    source: "external",
  },
  {
    barcode: "0075457131102",
    product_name: "Shrimp Chips",
    brand: "Calbee",
    allergens: ["shellfish", "gluten"],
    source: "manual",
  },
];

products.forEach((product) => {
  db.products.updateOne(
    { barcode: product.barcode },
    {
      $setOnInsert: {
        _id: UUID(),
        created_at: new Date(),
      },
      $set: {
        product_name: product.product_name,
        brand: product.brand,
        allergens: product.allergens,
        source: product.source,
      },
    },
    { upsert: true }
  );
});

// --- restaurants (real NYC coordinates; coordinates are [longitude, latitude]) ---
const restaurants = [
  {
    _id: "seed-resto-empire-state",
    resteraunt_name: "Green Fork Bistro",
    opening_times: ["Mon-Fri 11:00-22:00", "Sat-Sun 10:00-23:00"],
    location: {
      full_address: "350 5th Ave, New York, NY 10118",
      coordinates: [-73.9857, 40.7484],
    },
    website_url: "https://greenforkbistro.example.com",
    menu_items: [
      {
        item_name: "Garden Salad",
        category: "Starters",
        ingredients: ["lettuce", "tomato", "cucumber", "olive oil"],
        allergens: [],
      },
      {
        item_name: "Grilled Salmon",
        category: "Mains",
        ingredients: ["salmon", "butter", "lemon", "asparagus"],
        allergens: ["fish", "dairy"],
      },
      {
        item_name: "Peanut Satay Skewers",
        category: "Mains",
        ingredients: ["chicken", "peanut sauce", "rice"],
        allergens: ["peanuts", "soy"],
      },
    ],
    properties: { outdoor_seating: true, vegan_options: true, wheelchair_accessible: true },
  },
  {
    _id: "seed-resto-central-park-west",
    resteraunt_name: "Harbor & Vine",
    opening_times: ["Tue-Sun 12:00-22:30"],
    location: {
      full_address: "200 Central Park West, New York, NY 10024",
      coordinates: [-73.9738, 40.7813],
    },
    website_url: "https://harborandvine.example.com",
    menu_items: [
      {
        item_name: "Clam Chowder",
        category: "Starters",
        ingredients: ["clams", "cream", "potato", "celery"],
        allergens: ["shellfish", "dairy"],
      },
      {
        item_name: "Wagyu Burger",
        category: "Mains",
        ingredients: ["beef", "brioche bun", "cheddar", "egg mayo"],
        allergens: ["gluten", "dairy", "egg"],
      },
      {
        item_name: "Chocolate Lava Cake",
        category: "Desserts",
        ingredients: ["chocolate", "flour", "butter", "egg"],
        allergens: ["gluten", "dairy", "egg"],
      },
    ],
    properties: { outdoor_seating: false, vegan_options: false, wheelchair_accessible: true },
  },
  {
    _id: "seed-resto-rockefeller",
    resteraunt_name: "Uptown Noodle House",
    opening_times: ["Mon-Sun 11:30-21:30"],
    location: {
      full_address: "30 Rockefeller Plaza, New York, NY 10112",
      coordinates: [-73.9787, 40.7587],
    },
    website_url: null,
    menu_items: [
      {
        item_name: "Peanut Noodles",
        category: "Mains",
        ingredients: ["wheat noodles", "peanut sauce", "scallion"],
        allergens: ["gluten", "peanuts", "soy"],
      },
      {
        item_name: "Shrimp Dumplings",
        category: "Starters",
        ingredients: ["shrimp", "wheat wrapper", "ginger"],
        allergens: ["shellfish", "gluten"],
      },
      {
        item_name: "Mango Sticky Rice",
        category: "Desserts",
        ingredients: ["mango", "sticky rice", "coconut milk"],
        allergens: [],
      },
    ],
    properties: { outdoor_seating: false, vegan_options: true, wheelchair_accessible: false },
  },
  {
    _id: "seed-resto-world-trade",
    resteraunt_name: "Downtown Grill Co.",
    opening_times: ["Mon-Fri 07:00-20:00", "Sat 09:00-18:00"],
    location: {
      full_address: "1 World Trade Center, New York, NY 10007",
      coordinates: [-74.0134, 40.7127],
    },
    website_url: "https://downtowngrillco.example.com",
    menu_items: [
      {
        item_name: "Classic Omelette",
        category: "Breakfast",
        ingredients: ["egg", "cheese", "butter"],
        allergens: ["egg", "dairy"],
      },
      {
        item_name: "Almond Milk Latte",
        category: "Drinks",
        ingredients: ["espresso", "almond milk"],
        allergens: ["tree nuts"],
      },
      {
        item_name: "Steak Frites",
        category: "Mains",
        ingredients: ["beef", "potato", "butter"],
        allergens: ["dairy"],
      },
    ],
    properties: { outdoor_seating: true, vegan_options: false, wheelchair_accessible: true },
  },
];

restaurants.forEach((resto) => {
  db.resteraunts.updateOne(
    { _id: resto._id },
    {
      $set: {
        added_by: masterUserId,
        resteraunt_name: resto.resteraunt_name,
        opening_times: resto.opening_times,
        location: resto.location,
        website_url: resto.website_url,
        menu_items: resto.menu_items,
        properties: resto.properties,
      },
    },
    { upsert: true }
  );
});

print("Seed complete:");
print(`  users: ${db.users.countDocuments()}`);
print(`  products: ${db.products.countDocuments()}`);
print(`  resteraunts: ${db.resteraunts.countDocuments()}`);
print(`  master user email: master@allerscan.dev / password: Master123!`);
