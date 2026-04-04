import type React from 'react';

export interface NumberInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  className?: string;
}

export function NumberInput({ className = '', inputMode = 'numeric', ...rest }: NumberInputProps) {
  return <input type="number" inputMode={inputMode} className={`input-box ${className}`.trim()} {...rest} />;
}
