interface DrawerBackdropProps {
  isActive: boolean;
  onClick: () => void;
}

export function DrawerBackdrop({ isActive, onClick }: DrawerBackdropProps) {
  return <div className={`drawer-backdrop ${isActive ? 'active' : ''}`} onClick={onClick} />;
}
