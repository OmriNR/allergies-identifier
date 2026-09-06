import { Outlet } from "react-router-dom";
import TabBar from "@/components/TabBar";

export default function AppTabLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <main className="flex-1">
        <Outlet />
      </main>
      <TabBar />
    </div>
  );
}