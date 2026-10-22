import { Link } from "react-router";

export default function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2">
      <img src="/favicon.svg" alt="" className="h-8 w-8" />
      <span className="text-lg font-semibold tracking-wide text-ink">MONETA</span>
    </Link>
  );
}
