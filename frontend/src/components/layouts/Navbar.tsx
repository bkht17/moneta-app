import { useState } from "react";
import { HiOutlineMenu, HiOutlineX } from "react-icons/hi";

import Logo from "../ui/Logo";
import SideMenu from "./SideMenu";

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 flex items-center gap-5 border-b border-gray-200/50 bg-white px-7 py-4 backdrop-blur-[2px]">
      <button
        type="button"
        className="block cursor-pointer text-black min-[1080px]:hidden"
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Close menu" : "Open menu"}
      >
        {open ? <HiOutlineX className="text-2xl" /> : <HiOutlineMenu className="text-2xl" />}
      </button>
      <Logo />
      {open && (
        <div className="fixed top-[61px] left-0 bg-white shadow-lg min-[1080px]:hidden">
          <SideMenu onNavigate={() => setOpen(false)} />
        </div>
      )}
    </header>
  );
}
