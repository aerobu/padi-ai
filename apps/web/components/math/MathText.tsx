"use client";

/**
 * MathText — render a string with embedded math.
 *
 * Splits on `$...$` (inline) and `$$...$$` (display) delimiters and renders
 * each math segment with KaTeX. Plain-text segments are rendered verbatim.
 *
 * Used by QuestionCard so PRD Stage 1 § FR-11.2 KaTeX rendering works for
 * both questions and multiple-choice options.
 */

import "katex/dist/katex.min.css";
import { useMemo } from "react";
import katex from "katex";

interface MathSegment {
  type: "text" | "math";
  value: string;
  display?: boolean;
}

const MATH_RE = /(\$\$[^$]+\$\$|\$[^$]+\$)/g;

function splitSegments(input: string): MathSegment[] {
  if (!input) return [];
  const parts = input.split(MATH_RE);
  return parts.filter(Boolean).map((part) => {
    if (part.startsWith("$$") && part.endsWith("$$")) {
      return { type: "math", value: part.slice(2, -2), display: true };
    }
    if (part.startsWith("$") && part.endsWith("$")) {
      return { type: "math", value: part.slice(1, -1), display: false };
    }
    return { type: "text", value: part };
  });
}

export function MathText({ children, className }: { children: string; className?: string }) {
  const segments = useMemo(() => splitSegments(children), [children]);
  return (
    <span className={className}>
      {segments.map((seg, i) => {
        if (seg.type === "text") return <span key={i}>{seg.value}</span>;
        let html = "";
        try {
          html = katex.renderToString(seg.value, {
            throwOnError: false,
            displayMode: !!seg.display,
            output: "html",
          });
        } catch {
          html = `<span class="text-red-600">${seg.value}</span>`;
        }
        const Wrap = seg.display ? "div" : "span";
        return (
          <Wrap
            key={i}
            className={seg.display ? "my-2 block text-center" : "inline-block"}
            // eslint-disable-next-line react/no-danger
            dangerouslySetInnerHTML={{ __html: html }}
          />
        );
      })}
    </span>
  );
}
