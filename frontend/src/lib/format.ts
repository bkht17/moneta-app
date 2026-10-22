const kzt = new Intl.NumberFormat("ru-KZ", { maximumFractionDigits: 0 });

/** 35000 -> "35 000 ₸"; negative values keep their sign. */
export function formatKzt(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return "—";
  return `${kzt.format(Math.round(value))} ₸`;
}

export function parseIsoDate(iso: string) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function formatDay(iso: string | null | undefined) {
  if (!iso) return "—";
  return parseIsoDate(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

export function formatMonth(iso: string) {
  return parseIsoDate(iso).toLocaleDateString("en-GB", { month: "long", year: "numeric" });
}

export function firstOfMonth(date = new Date()) {
  const m = String(date.getMonth() + 1).padStart(2, "0");
  return `${date.getFullYear()}-${m}-01`;
}

export function getInitials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase())
    .join("");
}

/** Digits only, so "100 000" and "100,000" both become "100000". Empty stays empty. */
export function digitsOnly(value: string) {
  return value.replace(/\D/g, "");
}
