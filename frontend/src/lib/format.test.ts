import { describe, expect, it } from "vitest";

import { digitsOnly, firstOfMonth, formatKzt, getInitials } from "./format";

describe("format helpers", () => {
  it("formats tenge without decimals", () => {
    expect(formatKzt(65000).replace(/\s/g, " ")).toBe("65 000 ₸");
    expect(formatKzt(null)).toBe("—");
  });

  it("keeps an empty cash field empty instead of turning it into 0", () => {
    expect(digitsOnly("")).toBe("");
    expect(digitsOnly("8 000")).toBe("8000");
  });

  it("builds the first day of a month", () => {
    expect(firstOfMonth(new Date(2026, 9, 22))).toBe("2026-10-01");
  });

  it("makes initials", () => {
    expect(getInitials("Demo Student")).toBe("DS");
  });
});
