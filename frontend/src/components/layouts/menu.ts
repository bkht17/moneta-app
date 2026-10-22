import type { IconType } from "react-icons";
import { LuFilePlus2, LuHistory, LuLayoutDashboard, LuSettings } from "react-icons/lu";

export interface MenuItem {
  label: string;
  path: string;
  icon: IconType;
}

export const MENU: MenuItem[] = [
  { label: "Overview", path: "/", icon: LuLayoutDashboard },
  { label: "New review", path: "/reviews/new", icon: LuFilePlus2 },
  { label: "History", path: "/reviews", icon: LuHistory },
  { label: "Settings", path: "/settings", icon: LuSettings },
];
