import { InputHTMLAttributes, ForwardedRef, forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef(
  ({ label, error, className = '', ...props }: InputProps, ref: ForwardedRef<HTMLInputElement>) => {
    const inputStyles = `
      w-full px-3 py-2 border rounded-md
      focus:outline-none focus:ring-2 focus:ring-padiGreen-500 focus:border-transparent
      disabled:opacity-50 disabled:cursor-not-allowed
      ${error ? 'border-error-500' : 'border-gray-300'}
      ${className}
    `.trim();

    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {label}
          </label>
        )}
        <input ref={ref} className={inputStyles} {...props} />
        {error && (
          <p className="mt-1 text-sm text-error-600">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
