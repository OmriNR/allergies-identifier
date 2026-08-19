import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, CheckCircle2, AlertTriangle, Loader2, RotateCcw } from "lucide-react";
import * as scansApi from "@/api/scans";
import { useAuth } from "@/lib/AuthContext";
import type { ScanHistoryItem } from "@/api/userProperties";

export default function Alert() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [params] = useSearchParams();
  const barcode = params.get("barcode");

  const [loading, setLoading] = useState<boolean>(true);
  const [result, setResult] = useState<ScanHistoryItem | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    if (!barcode) {
      setError("No barcode provided.");
      setLoading(false);
      return;
    }
    if (!user) {
      setError("You must be logged in to scan a product.");
      setLoading(false);
      return;
    }
    (async () => {
      try {
        const { historyEntry } = await scansApi.scanProduct(user.id, barcode);
        setResult(historyEntry);
      } catch {
        setError("Could not check this product. Please try again.");
      } finally {
        setLoading(false);
      }
    })();
  }, [barcode, user]);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <p className="text-sm text-muted-foreground">Checking product against your allergies…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-md px-5 py-10 text-center">
        <p className="text-sm text-destructive">{error}</p>
        <button
          onClick={() => navigate("/")}
          className="mt-4 text-sm text-muted-foreground underline"
        >
          Back to scan
        </button>
      </div>
    );
  }

  if (!result) return null;

  const dangerous = result.status === "dangerous";

  return (
    <div className={"min-h-screen " + (dangerous ? "bg-red-50" : "bg-emerald-50")}>
      <div className="mx-auto max-w-md px-5 py-8">
        <button
          onClick={() => navigate("/")}
          className={
            "mb-6 inline-flex items-center gap-1 text-sm " +
            (dangerous
              ? "text-red-700/70 hover:text-red-700"
              : "text-emerald-700/70 hover:text-emerald-700")
          }
        >
          <ArrowLeft className="h-4 w-4" /> Back
        </button>

        <div
          className={
            "flex flex-col items-center text-center " +
            (dangerous ? "text-red-700" : "text-emerald-700")
          }
        >
          <div
            className={
              "flex h-20 w-20 items-center justify-center rounded-full " +
              (dangerous ? "bg-red-100" : "bg-emerald-100")
            }
          >
            {dangerous ? (
              <AlertTriangle className="h-10 w-10" />
            ) : (
              <CheckCircle2 className="h-10 w-10" />
            )}
          </div>
          <h1 className="mt-4 text-2xl font-semibold tracking-tight">
            {dangerous ? "Unsafe for you" : "Safe for you"}
          </h1>
          <p className="mt-1 text-sm opacity-80">
            {dangerous
              ? "This product contains allergens you avoid."
              : "No matching allergens were detected."}
          </p>
        </div>

        <div className="mt-8 rounded-2xl bg-white p-5 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Product</p>
          <p className="mt-1 text-lg font-medium">{result.product_name}</p>
          {result.brand && <p className="text-sm text-muted-foreground">{result.brand}</p>}
          <div className="mt-3 border-t border-border pt-3">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Barcode</p>
            <p className="mt-1 font-mono text-sm">{barcode}</p>
          </div>
        </div>

        {dangerous && (
          <div className="mt-4 rounded-2xl border border-red-200 bg-white p-5">
            <p className="text-sm font-medium text-red-700">Detected allergens</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {(result.detected_allergens ?? []).map((a) => (
                <span
                  key={a}
                  className="rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-700"
                >
                  {a}
                </span>
              ))}
            </div>
          </div>
        )}

        <button
          onClick={() => navigate("/")}
          className={
            "mt-8 inline-flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-medium text-white " +
            (dangerous ? "bg-red-600 hover:bg-red-700" : "bg-emerald-600 hover:bg-emerald-700")
          }
        >
          <RotateCcw className="h-4 w-4" /> Scan another product
        </button>
      </div>
    </div>
  );
}