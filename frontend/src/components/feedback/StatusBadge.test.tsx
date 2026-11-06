import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders status text and formats underscores", () => {
    render(<StatusBadge status="more_info_required" />);
    expect(screen.getByText("more info required")).toBeInTheDocument();
  });

  it("applies correct variant styling for success statuses", () => {
    const { container } = render(<StatusBadge status="complete" />);
    const badge = container.querySelector("span");
    expect(badge).not.toBeNull();
    expect(badge?.className).toContain("success");
  });

  it("applies correct variant styling for danger statuses", () => {
    const { container } = render(<StatusBadge status="archived" />);
    const badge = container.querySelector("span");
    expect(badge?.className).toContain("danger");
  });

  it("applies correct variant styling for warning statuses", () => {
    const { container } = render(<StatusBadge status="draft" />);
    const badge = container.querySelector("span");
    expect(badge?.className).toContain("warning");
  });
});
