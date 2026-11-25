// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";
import { App } from "./App";

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

describe("ScruCheckAI Application", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  it("defaults to light mode on first visit and toggles theme", () => {
    render(<App />);
    expect(document.documentElement.classList.contains("dark")).toBe(false);
    expect(screen.getByText("Scru-Check-AI")).toBeInTheDocument();

    const toggleBtn = screen.getByRole("button", { name: /switch to dark mode/i });
    fireEvent.click(toggleBtn);
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(localStorage.getItem("scrucheck_theme")).toBe("dark");
  });

  it("enforces PDF and DOCX upload validation", () => {
    render(<App />);
    const input = document.getElementById("file-upload") as HTMLInputElement;
    const badFile = new File(["hello"], "notes.txt", { type: "text/plain" });
    fireEvent.change(input, { target: { files: [badFile] } });
    expect(screen.getByText(/Security Policy Violation/i)).toBeInTheDocument();
  });
});
