import { Button, DrawerBody, DrawerFooter, DrawerHeader, DrawerShell, ToggleSwitch } from '@vistaflow/ui';
import type { JourneyViewPrefs } from '@/stores/uiStore';

interface JourneyViewDrawerProps {
  isOpen: boolean;
  prefs: JourneyViewPrefs;
  onChange: (patch: Partial<JourneyViewPrefs>) => void;
  onClose: () => void;
}

export function JourneyViewDrawer({
  isOpen,
  prefs,
  onChange,
  onClose,
}: JourneyViewDrawerProps) {
  return (
    <DrawerShell open={isOpen}>
      <DrawerHeader
        eyebrow={'\u66f4\u591a\u7b5b\u9009'}
        title={'\u7ed3\u679c\u8fc7\u6ee4'}
        subtitle={'\u8fd9\u91cc\u4fdd\u7559\u4f4e\u9891\u4f46\u4ecd\u7136\u6709\u4ef7\u503c\u7684\u8fc7\u6ee4\u9879\uff0c\u4e0d\u4f1a\u91cd\u65b0\u89e6\u53d1\u641c\u7d22\u3002'}
        onClose={onClose}
        closeLabel={'\u5173\u95ed\u7ed3\u679c\u8fc7\u6ee4'}
      />

      <DrawerBody>
        <section className="vf-drawer-group">
          <div className="vf-drawer-toggle-row">
            <span className="vf-drawer-toggle-row__title">{'\u8fc7\u6ee4\u4e0e\u76f4\u8fbe\u91cd\u590d\u8f66\u6b21\u7684\u4e2d\u8f6c\u65b9\u6848'}</span>
            <ToggleSwitch
              checked={prefs.excludeDirectTrainCodesInTransferRoutes}
              onChange={(value) =>
                onChange({ excludeDirectTrainCodesInTransferRoutes: value })
              }
            />
          </div>
          <p className="vf-drawer-meta">
            {'\u57fa\u4e8e\u5b8c\u6574\u5019\u9009\u6c60\uff0c\u53bb\u6389\u548c\u76f4\u8fbe\u8f66\u6b21\u91cd\u590d\u7684\u4e2d\u8f6c\u65b9\u6848\u3002'}
          </p>
        </section>
      </DrawerBody>

      <DrawerFooter>
        <Button variant="primary" onClick={onClose}>
          {'\u5b8c\u6210'}
        </Button>
      </DrawerFooter>
    </DrawerShell>
  );
}
