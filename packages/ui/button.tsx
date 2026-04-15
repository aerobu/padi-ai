import { ReactNode } from 'react';

interface ButtonProps {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  onClick,
  type = 'button',
  className = '',
}: ButtonProps) {
  // Design spec Section 6.1: 48px (student), 40px (dashboard)
  // Press feedback: scale(0.96) for duration-fast (200ms)
  const baseStyles =
    'inline-flex items-center justify-center font-medium rounded-md transition-all duration-200 active:scale-96 focus:outline-none focus:ring-2 focus:ring-offset-2';

  const variants = {
    // Primary brand color is teal per design system
    primary:
      'bg-teal-600 text-white hover:bg-teal-700 focus:ring-teal-500',
    // Secondary uses warm accent for celebration/engagement
    secondary:
      'bg-warm-500 text-white hover:bg-warm-600 focus:ring-warm-400',
    outline:
      'border-2 border-teal-600 text-teal-600 hover:bg-teal-50 focus:ring-teal-500',
    ghost:
      'text-neutral-700 hover:bg-neutral-100 focus:ring-neutral-500',
  };

  // Sizes from design spec: lg=48px (student), md=40px (dashboard), sm=32px
  const sizes = {
    sm: 'px-3 py-2 text-label-sm', // 32px
    md: 'px-4 py-2.5 text-label-sm', // 40px (dashboard)
    lg: 'px-6 h-12 text-label-lg', // 48px (student)
  };

  const disabledStyles = disabled || loading
    ? 'opacity-50 cursor-not-allowed'
    : 'cursor-pointer';

  return (
    <button
      type={type}
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${disabledStyles} ${className}`}
      disabled={disabled || loading}
      onClick={onClick}
    >
      {loading && (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      )}
      {children}
    </button>
  );
}
