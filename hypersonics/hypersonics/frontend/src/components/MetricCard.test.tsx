import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MetricCard } from "./MetricCard";

describe("MetricCard", () => {
  it("renders a labeled aerospace metric", () => {
    render(<MetricCard label="Wall Temp" value="1490 K" tone="guarded" />);

    expect(screen.getByText("Wall Temp")).toBeInTheDocument();
    expect(screen.getByText("1490 K")).toBeInTheDocument();
  });

  it("applies the risk tone class", () => {
    const { container } = render(<MetricCard label="Risk" value="Critical" tone="critical" />);

    expect(container.firstElementChild).toHaveClass("metric-critical");
  });
});
