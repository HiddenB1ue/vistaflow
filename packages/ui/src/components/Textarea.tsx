import type React from 'react';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  className?: string;
}

export function Textarea({ className = '', ...rest }: TextareaProps) {
  return <textarea className={`input-box vf-textarea ${className}`.trim()} {...rest} />;
}
