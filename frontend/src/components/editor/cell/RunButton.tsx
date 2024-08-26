/* Copyright 2024 Marimo. All rights reserved. */
import { HardDriveDownloadIcon, PlayIcon, SquareIcon } from "lucide-react";
import { Button } from "@/components/editor/inputs/Inputs";
import { Tooltip } from "../../ui/tooltip";
import { renderShortcut } from "../../shortcuts/renderShortcut";
import { cn } from "../../../utils/cn";
import { sendInterrupt } from "@/core/network/requests";
import { useShouldShowInterrupt } from "./useShouldShowInterrupt";
import type { RuntimeState, CellConfig } from "@/core/network/types";

function computeColor(
  appClosed: boolean,
  needsRun: boolean,
  loading: boolean,
  inactive: boolean,
) {
  if (appClosed) {
    return "disabled";
  }
  if (needsRun && !loading) {
    return "yellow";
  }
  if (loading || inactive) {
    return "disabled";
  }
  return "hint-green";
}

export const RunButton = (props: {
  edited: boolean;
  status: RuntimeState;
  needsRun: boolean;
  appClosed: boolean;
  config: CellConfig;
  onClick?: () => void;
}): JSX.Element => {
  const { onClick, appClosed, needsRun, status, config, edited } = props;

  const blockedStatus = status === "disabled-transitively";
  const loading = status === "running" || status === "queued";
  const inactive =
    appClosed || loading || (!config.disabled && blockedStatus && !edited);
  const color = computeColor(appClosed, needsRun, loading, inactive);
  const running = status === "running";

  // Show the interrupt button after 200ms to avoid flickering.
  const showInterrupt = useShouldShowInterrupt(running);

  if (config.disabled) {
    return (
      <Tooltip content="Add code to notebook" usePortal={false}>
        <Button
          className={cn(
            !needsRun && "hover-action",
            inactive && "inactive-button",
          )}
          onClick={onClick}
          color={color}
          shape="circle"
          size="small"
          data-testid="run-button"
        >
          <HardDriveDownloadIcon strokeWidth={1.8} />
        </Button>
      </Tooltip>
    );
  }
  if (!config.disabled && blockedStatus && !edited) {
    return (
      <Tooltip
        content="This cell can't be run because it has a disabled ancestor"
        usePortal={false}
      >
        <Button
          className={cn(
            !needsRun && "hover-action",
            inactive && "inactive-button",
          )}
          onClick={onClick}
          color={color}
          shape="circle"
          size="small"
          data-testid="run-button"
        >
          <PlayIcon strokeWidth={1.8} />
        </Button>
      </Tooltip>
    );
  }

  if (showInterrupt) {
    return (
      <Tooltip content={renderShortcut("global.interrupt")} usePortal={false}>
        <Button
          className={cn(appClosed && "inactive-button")}
          onClick={sendInterrupt}
          color="yellow"
          shape="circle"
          size="small"
          data-testid="run-button"
        >
          <SquareIcon strokeWidth={1.5} />
        </Button>
      </Tooltip>
    );
  }

  let tooltipMsg: React.ReactNode = "";
  if (appClosed) {
    tooltipMsg = "App disconnected";
  } else if (status === "queued") {
    tooltipMsg = "This cell is already queued to run";
  } else {
    tooltipMsg = renderShortcut("cell.run");
  }

  return (
    <Tooltip content={tooltipMsg} usePortal={false}>
      <Button
        className={cn(
          !needsRun && "hover-action",
          inactive && "inactive-button",
        )}
        onClick={onClick}
        color={color}
        shape="circle"
        size="small"
        data-testid="run-button"
      >
        <PlayIcon strokeWidth={1.8} />
      </Button>
    </Tooltip>
  );
};
