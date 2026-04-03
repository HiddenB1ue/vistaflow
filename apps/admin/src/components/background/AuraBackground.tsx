export function AuraBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none" style={{ zIndex: 0 }}>
      <div className="absolute rounded-full" style={{
        width: '60vw', height: '60vw', top: '-10%', left: '-10%',
        background: 'radial-gradient(circle, #110e24 0%, transparent 70%)',
        filter: 'blur(120px)', opacity: 0.18,
      }} />
      <div className="absolute rounded-full" style={{
        width: '40vw', height: '40vw', bottom: '-10%', right: '-5%',
        background: 'radial-gradient(circle, rgba(139,92,246,0.2) 0%, transparent 70%)',
        filter: 'blur(120px)', opacity: 0.18,
      }} />
    </div>
  );
}
