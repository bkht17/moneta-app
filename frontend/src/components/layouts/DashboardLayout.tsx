import { Navigate, Outlet } from "react-router";

import { useAuth } from "../../context/AuthContext";
import Spinner from "../ui/Spinner";
import Navbar from "./Navbar";
import SideMenu from "./SideMenu";

export default function DashboardLayout() {
  const { user, loading } = useAuth();

  if (loading) return <Spinner />;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div>
      <Navbar />
      <div className="flex">
        <div className="max-[1080px]:hidden">
          <SideMenu />
        </div>
        <main className="mx-5 my-5 min-w-0 grow">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
