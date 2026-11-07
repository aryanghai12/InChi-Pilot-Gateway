import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Button } from "./Button";

describe("Button", () => {
  it("renders children text", () => {
    render(<Button>Click Me</Button>);
    expect(screen.getByRole("button", { name: "Click Me" })).toBeInTheDocument();
  });

  it("shows loading text and is disabled when isLoading is true", () => {
    render(<Button isLoading>Submit</Button>);
    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
    expect(button).toHaveTextContent("Please wait...");
  });

  it("is disabled when disabled prop is passed", () => {
    render(<Button disabled>Disabled Action</Button>);
    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
  });
});
