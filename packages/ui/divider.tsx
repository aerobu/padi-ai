"use client";

import { cn } from "@/lib/utils";

export function Divider({ className }: { className?: string }) {
  return <hr className={cn("border-t border-neutral-200 my-3", className)} />;
}
