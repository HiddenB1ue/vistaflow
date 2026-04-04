
import { Button, DrawerBody, DrawerFooter, DrawerHeader, DrawerShell, ToggleSwitch } from '@vistaflow/ui';
import { FILTER_LABELS } from '@/constants/labels';

interface FilterDrawerProps {
  isOpen: boolean;
  directOnly: boolean;
  business: boolean;
  first: boolean;
  second: boolean;
  onDirectOnlyChange: (value: boolean) => void;
  onBusinessChange: (value: boolean) => void;
  onFirstChange: (value: boolean) => void;
  onSecondChange: (value: boolean) => void;
  onClose: () => void;
}

const seatOptions = [
  { key: 'business', label: FILTER_LABELS.business },
  { key: 'first', label: FILTER_LABELS.first },
  { key: 'second', label: FILTER_LABELS.second },
] as const;

export function FilterDrawer({
  isOpen,
  directOnly,
  business,
  first,
  second,
  onDirectOnlyChange,
  onBusinessChange,
  onFirstChange,
  onSecondChange,
  onClose,
}: FilterDrawerProps) {
  const toggles = {
    business: { value: business, onChange: onBusinessChange },
    first: { value: first, onChange: onFirstChange },
    second: { value: second, onChange: onSecondChange },
  } as const;

  return (
    <DrawerShell open={isOpen}>
      <DrawerHeader
        eyebrow={FILTER_LABELS.eyebrow}
        title={FILTER_LABELS.title}
        subtitle={FILTER_LABELS.subtitle}
        onClose={onClose}
        closeLabel="关闭偏好设置"
      />

      <DrawerBody>
        <section className="vf-drawer-group">
          <div className="vf-drawer-toggle-row">
            <span className="vf-drawer-toggle-row__title">{FILTER_LABELS.directOnly}</span>
            <ToggleSwitch checked={directOnly} onChange={onDirectOnlyChange} />
          </div>
          <p className="vf-drawer-meta">{FILTER_LABELS.directOnlyDesc}</p>
        </section>

        <section className="vf-drawer-group">
          <div className="vf-drawer-label">{FILTER_LABELS.seatPreference}</div>
          <div className="space-y-5 text-sm text-starlight">
            {seatOptions.map(({ key, label }) => (
              <div key={key} className="vf-drawer-toggle-row">
                <span>{label}</span>
                <ToggleSwitch checked={toggles[key].value} onChange={toggles[key].onChange} />
              </div>
            ))}
          </div>
        </section>
      </DrawerBody>

      <DrawerFooter>
        <Button variant="primary" onClick={onClose}>{FILTER_LABELS.saveButton}</Button>
      </DrawerFooter>
    </DrawerShell>
  );
}
