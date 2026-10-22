import type { ReactNode } from "react";
import { LuLayers, LuShieldCheck, LuWallet } from "react-icons/lu";

import Logo from "../ui/Logo";

const POINTS = [
  { icon: LuLayers, title: "Kaspi, Halyk and cash in one total", text: "Upload your PDF statements and add what you spent in cash." },
  { icon: LuWallet, title: "See what is left of your budget", text: "Remaining budget for the dates every source covers." },
  { icon: LuShieldCheck, title: "Your statements are not kept", text: "PDFs are read once and discarded. Only card endings are saved." },
];

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <div className="flex w-full flex-col px-8 pt-8 pb-12 md:w-[60vw] md:px-12">
        <Logo />
        <div className="flex grow items-center">{children}</div>
      </div>

      <aside className="relative hidden w-[40vw] overflow-hidden bg-primary p-10 text-white md:flex md:flex-col md:justify-center">
        <div className="absolute -top-10 -right-10 h-48 w-48 rounded-[40px] bg-lime/20" />
        <div className="absolute -bottom-12 -left-8 h-56 w-56 rounded-[40px] border-[18px] border-lime/30" />
        <h2 className="relative mb-8 text-3xl leading-tight font-semibold">
          One view of this month&apos;s spending across your banks and cash
        </h2>
        <ul className="relative space-y-5">
          {POINTS.map((p) => (
            <li key={p.title} className="flex gap-4 rounded-2xl bg-white/10 p-4">
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-lime text-xl text-ink">
                <p.icon />
              </span>
              <span>
                <span className="block font-medium">{p.title}</span>
                <span className="text-sm text-white/80">{p.text}</span>
              </span>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}
