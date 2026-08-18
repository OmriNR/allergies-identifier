import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck, History, Settings } from "lucide-react";
import { base44 } from "@/api/base44Client";
import BarcodeScanner from "@/components/BarcodeScanner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface ScanItem {
  id: string;
  barcode: string;
  product_name: string;
  status: "safe" | "dangerous";
  detected_allergens?: string[];
  brand?: string;
}

export default function Home() {
  const navigate = useNavigate();
  const [history, setHistory] = useState<ScanItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    base44.entities.ScanHistory.list("-created_date", 5)
      .then((items: ScanItem[]) => setHistory(items))
      .finally(() => setLoading(false));
  }, []);

  const handleScan = (barcode: string) => {
    if (barcode) navigate(`/alert?barcode=${encodeURIComponent(barcode)}`);
  };

  return (
    <div className="mx-auto max-w-md px-5 py-8">
      <header className="mb-8 text-center">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary">
          <ShieldCheck className="h-6 w-6 text-primary-foreground" />
        </div>
        <h1 className="text-2xl font-semibold tracking-tight">AllerScan</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Scan a product barcode to check it against your allergies.
        </p>
      </header>

      <Card className="border-0 shadow-sm">
        <div className="p-6">
          <BarcodeScanner onScan={handleScan} />
        </div>
      </Card>

      <div className="mt-8 flex gap-3">
        <Button variant="outline" className="flex-1" onClick={() => navigate("/preferences")}>
          <Settings className="mr-2 h-4 w-4" /> My allergies
        </Button>
      </div>

      <section className="mt-10">
        <div className="mb-3 flex items-center gap-2">
          <History className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-medium text-muted-foreground">Recent scans</h2>
        </div>
        {loading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-14 animate-pulse rounded-xl bg-muted" />
            ))}
          </div>
        ) : history.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            No scans yet. Scan your first product above.
          </p>
        ) : (
          <div className="space-y-2">
            {history.map((item) => (
              <button
                key={item.id}
                onClick={() => navigate(`/alert?barcode=${encodeURIComponent(item.barcode)}`)}
                className="flex w-full items-center justify-between rounded-xl border border-border bg-card p-3 text-left transition-colors hover:bg-accent"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{item.product_name}</p>
                  <p className="truncate text-xs text-muted-foreground">{item.barcode}</p>
                </div>
                <span
                  className={
                    "ml-3 shrink-0 rounded-full px-2.5 py-1 text-xs font-medium " +
                    (item.status === "safe"
                      ? "bg-emerald-50 text-emerald-700"
                      : "bg-red-50 text-red-700")
                  }
                >
                  {item.status === "safe" ? "Safe" : "Unsafe"}
                </span>
              </button>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}