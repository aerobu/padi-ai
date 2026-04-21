import * as React from "react";
import { cn } from "@/lib/utils";

// Card
interface CardProps {
  className?: string;
  children: React.ReactNode;
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, children }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-lg border bg-white text-gray-950 shadow dark:bg-gray-950 dark:text-gray-50",
          className
        )}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";

// CardHeader
interface CardHeaderProps {
  className?: string;
  children: React.ReactNode;
}

const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, children }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("flex flex-col space-y-1.5 p-6", className)}
      >
        {children}
      </div>
    );
  }
);

CardHeader.displayName = "CardHeader";

// CardTitle
interface CardTitleProps {
  className?: string;
  children: React.ReactNode;
}

const CardTitle = React.forwardRef<HTMLParagraphElement, CardTitleProps>(
  ({ className, children }, ref) => {
    return (
      <h3
        ref={ref}
        className={cn(
          "text-2xl font-semibold leading-none tracking-tight",
          className
        )}
      >
        {children}
      </h3>
    );
  }
);

CardTitle.displayName = "CardTitle";

// CardDescription
interface CardDescriptionProps {
  className?: string;
  children: React.ReactNode;
}

const CardDescription = React.forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ className, children }, ref) => {
    return (
      <p
        ref={ref}
        className={cn("text-sm text-gray-500 dark:text-gray-400", className)}
      >
        {children}
      </p>
    );
  }
);

CardDescription.displayName = "CardDescription";

// CardContent
interface CardContentProps {
  className?: string;
  children: React.ReactNode;
}

const CardContent = React.forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, children }, ref) => {
    return (
      <div ref={ref} className={cn("p-6 pt-0", className)}>
        {children}
      </div>
    );
  }
);

CardContent.displayName = "CardContent";

// CardFooter
interface CardFooterProps {
  className?: string;
  children: React.ReactNode;
}

const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, children }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("flex items-center p-6 pt-0", className)}
      >
        {children}
      </div>
    );
  }
);

CardFooter.displayName = "CardFooter";

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
};

export type {
  CardProps,
  CardHeaderProps,
  CardFooterProps,
  CardTitleProps,
  CardDescriptionProps,
  CardContentProps,
};
