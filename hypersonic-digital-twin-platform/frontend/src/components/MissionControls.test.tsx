import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { defaultMission } from "../state/defaultMission";
import { MissionControls } from "./MissionControls";

describe("MissionControls", () => {
  it("starts the digital twin mission from the primary action", async () => {
    const user = userEvent.setup();
    const onStart = vi.fn();

    render(<MissionControls mission={defaultMission} running={false} onStart={onStart} />);

    await user.click(screen.getByRole("button", { name: /run digital twin mission/i }));

    expect(onStart).toHaveBeenCalledTimes(1);
  });

  it("shows streaming state while mission is running", () => {
    render(<MissionControls mission={defaultMission} running={true} onStart={vi.fn()} />);

    expect(screen.getByRole("button", { name: /streaming mission/i })).toBeInTheDocument();
  });
});
