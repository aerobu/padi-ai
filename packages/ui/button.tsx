"use client";

import { type VariantProps, cva } from "class-variance-authority";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "@/lib/utils";
import { Spinner } from "./spinner";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap font-semibold transition-all will-change-[transform,background-color,box-shadow,opacity] outline-none ring-2 ring-offset-2 ring-offset-white dark:ring-offset-gray-950",
  {
    variants: {
      variant: {
        primary:   "bg-terra-500 text-white shadow-[0_4px_12px_rgba(191,110,60,.28)] hover:bg-terra-600 active:scale-[.96]",
        secondary: "bg-green-600 text-white shadow-[0_8px_24px_-4px_rgba(45,95,74,.4)] hover:bg-green-700 active:scale-[.96]",
        outline:   "bg-transparent text-neutral-700 border-[1.5px] border-neutral-300 hover:bg-neutral-100 hover:border-neutral-500 active:scale-[.96]",
        ghost:     "bg-transparent text-neutral-600 hover:bg-neutral-100 hover:text-neutral-800 active:scale-[.96]",
        link:      "text-terra-600 underline-offset-4 hover:underline active:scale-[.96]",
        // shell-only variants
        terraFull: "bg-terra-500 text-white shadow-[0_4px_12px_rgba(191,110,60,.28)] hover:bg-terra-600 active:scale-[.96] w-full rounded-xl h-[52px] text-[15px] tracking-[.01em]",
      },
      size: {
        lg: "h-[48px] px-6 rounded-md text-[15px]",
        md: "h-[40px] px-5 rounded-md text-[14px]",
        sm: "h-[32px] px-4 rounded-sm text-[12px]",
      },
    },
    defaultVariants: {
      variant: "primary",
      size:    "md",
    },
  }
);

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
}

export function Button({
  variant = "primary",
  size = "md",
  className,
  asChild = false,
  loading = false,
  disabled,
  children,
  ...props
}: ButtonProps) {
  const Component = asChild ? Slot : "button";
  return (
    <Component
      className={cn(buttonVariants({ variant, size, className }))}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Spinner size="sm" className="text-current" />}
      {children}
    </Component>
  );
}
