interface InputBoxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  className?: string;
}

export function InputBox({ className = '', ...rest }: InputBoxProps) {
  return <input className={`input-box ${className}`} {...rest} />;
}
