/* Copyright 2024 Marimo. All rights reserved. */
import { memo, useState } from "react";
import {
  type DataType,
  JsonViewer,
  booleanType,
  defineDataType,
  nullType,
} from "@textea/json-viewer";

import { HtmlOutput } from "./HtmlOutput";
import { ImageOutput } from "./ImageOutput";
import { TextOutput } from "./TextOutput";
import { VideoOutput } from "./VideoOutput";
import { logNever } from "../../../utils/assertNever";
import { useTheme } from "../../../theme/useTheme";

interface Props {
  /**
   * The data to display
   */
  data: unknown;

  format?: "auto" | "tree" | "raw";

  /**
   * A text label for the JSON viewer. If `false`, no label is used.
   */
  name?: string | false;

  className?: string;
}

/**
 * Output component for JSON data.
 */
export const JsonOutput: React.FC<Props> = memo(
  ({ data, format = "auto", name = false, className }) => {
    const { theme } = useTheme();
    if (format === "auto") {
      format = inferBestFormat(data);
    }

    switch (format) {
      case "tree":
        return (
          <JsonViewer
            className="marimo-json-output"
            rootName={name}
            theme={theme}
            displayDataTypes={false}
            value={data}
            style={{
              backgroundColor: "transparent",
            }}
            valueTypes={VALUE_TYPE}
            // disable array grouping (it's misleading) by using a large value
            groupArraysAfterLength={1_000_000}
            // TODO(akshayka): disable clipboard until we have a better
            // solution: copies raw values, shifts content; can use onCopy prop
            // to override what is copied to clipboard
            enableClipboard={false}
          />
        );
      case "raw":
        return <pre className={className}>{JSON.stringify(data, null, 2)}</pre>;
      default:
        logNever(format);
        return <pre className={className}>{JSON.stringify(data, null, 2)}</pre>;
    }
  },
);
JsonOutput.displayName = "JsonOutput";

function inferBestFormat(data: unknown): "tree" | "raw" {
  return typeof data === "object" && data !== null ? "tree" : "raw";
}

// Text with length > 500 is collapsed by default, and can be expanded by clicking on it.
const CollapsibleTextOutput = (props: { text: string }) => {
  const [isCollapsed, setIsCollapsed] = useState(true);
  return (
    <span className="cursor-pointer">
      {isCollapsed ? (
        <span onClick={() => setIsCollapsed(false)}>
          {props.text.slice(0, 500)}
          {props.text.length > 500 && "..."}
        </span>
      ) : (
        <span onClick={() => setIsCollapsed(true)}>{props.text}</span>
      )}
    </span>
  );
};

/**
 * Map from mimetype-prefix to render function.
 *
 * Render function takes leaf data as input.
 */
const LEAF_RENDERERS = {
  "image/": (value: string) => <ImageOutput src={value} />,
  "video/": (value: string) => <VideoOutput src={value} />,
  "text/html": (value: string) => <HtmlOutput html={value} inline={true} />,
  "text/plain+float:": (value: string) => <span>{value}</span>,
  "text/plain": (value: string) => <CollapsibleTextOutput text={value} />,
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MIME_TYPES: Array<DataType<any>> = Object.entries(LEAF_RENDERERS).map(
  ([leafType, render]) => ({
    is: (value) => typeof value === "string" && value.startsWith(leafType),
    Component: (props) => renderLeaf(props.value, render),
  }),
);

const PYTHON_BOOLEAN_TYPE = defineDataType<boolean>({
  ...booleanType,
  Component: ({ value }) => <span>{value ? "True" : "False"}</span>,
});

const PYTHON_NONE_TYPE = defineDataType<null>({
  ...nullType,
  Component: () => <span>None</span>,
});

const VALUE_TYPE = [...MIME_TYPES, PYTHON_BOOLEAN_TYPE, PYTHON_NONE_TYPE];

function leafData(leaf: string): string {
  const delimIndex = leaf.indexOf(":");
  if (delimIndex === -1) {
    throw new Error("Invalid leaf");
  }
  return leaf.slice(delimIndex + 1);
}

/**
 * Render a leaf.
 *
 * Leaf must have the format
 *
 *   <mimetype>:<data>
 *
 * where mimetype cannot contain ":".
 */
function renderLeaf(
  leaf: string,
  render: (data: string) => JSX.Element,
): JSX.Element {
  try {
    return render(leafData(leaf));
  } catch {
    return <TextOutput text={`Invalid leaf: ${leaf}`} />;
  }
}
