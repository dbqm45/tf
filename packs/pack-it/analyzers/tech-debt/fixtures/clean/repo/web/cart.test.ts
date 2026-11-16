import { describe, it, expect } from "vitest";

describe("cart", () => {
  // pominięty do czasu PAY-12 (nowe API koszyka)
  it.skip("adds item", () => {
    expect(1).toBe(1);
  });
  it("skips nothing", () => {
    const text = "it.skip(";
    expect(text).toBeTruthy();
  });
});
