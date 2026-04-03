export interface ToggleSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
}

export function ToggleSwitch({ checked, onChange }: ToggleSwitchProps) {
  return (
    <div
      className={`custom-toggle ${checked ? 'active' : ''}`}
      onClick={() => onChange(!checked)}
      role="switch"
      aria-checked={checked}
      tabIndex={0}
    />
  );
}
