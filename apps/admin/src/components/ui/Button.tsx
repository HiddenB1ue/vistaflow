type ButtonVariant = 'primary' | 'outline' | 'danger' | 'warning' | 'success';
type ButtonSize = 'default' | 'sm';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: React.ReactNode;
}

export function Button({ variant = 'outline', size = 'default', children, className = '', ...rest }: ButtonProps) {
  const cls = `btn btn-${variant} ${size === 'sm' ? 'btn-sm' : ''} ${className}`;
  return <button className={cls} {...rest}>{children}</button>;
}
