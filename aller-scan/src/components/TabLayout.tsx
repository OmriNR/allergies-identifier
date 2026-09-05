import { Outlet } from "react-router-dom";
import BottomNav from "@/components/BottomNav";

export default function TabLayout() {
  return (
    <div className="flex h-dvh flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto">
        <Outlet />
      </div>
      <BottomNav />
    </div>
  );
}
