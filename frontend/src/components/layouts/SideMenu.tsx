import { LuLogOut } from "react-icons/lu";
import { NavLink, useNavigate } from "react-router";

import { useAuth } from "../../context/AuthContext";
import CharAvatar from "../cards/CharAvatar";
import { MENU } from "./menu";

export default function SideMenu({ onNavigate }: { onNavigate?: () => void }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <nav className="sticky top-[61px] z-20 h-[calc(100vh-61px)] w-64 border-r border-gray-200/50 bg-white p-5">
      <div className="mt-3 mb-7 flex flex-col items-center justify-center gap-3">
        <CharAvatar fullName={user?.full_name || user?.email || ""} className="h-20 w-20 text-xl" />
        <h5 className="text-center leading-6 font-medium text-gray-950">{user?.full_name || user?.email}</h5>
      </div>

      {MENU.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          end
          onClick={onNavigate}
          className={({ isActive }) =>
            `mb-3 flex w-full items-center gap-4 rounded-lg px-6 py-3 text-[15px] ${
              isActive ? "bg-primary text-white" : "hover:bg-mint"
            }`
          }
        >
          <item.icon className="text-xl" />
          {item.label}
        </NavLink>
      ))}

      <button
        type="button"
        className="mb-3 flex w-full cursor-pointer items-center gap-4 rounded-lg px-6 py-3 text-[15px] hover:bg-mint"
        onClick={() => {
          logout();
          navigate("/login");
        }}
      >
        <LuLogOut className="text-xl" />
        Log out
      </button>
    </nav>
  );
}
