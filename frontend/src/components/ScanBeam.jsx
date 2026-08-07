export default function ScanBeam() {
  return (
    <div
      className="relative overflow-hidden rounded-lg border p-8"
      style={{ borderColor: 'var(--ink-line)', background: 'var(--ink-raised)' }}
    >
      <div
        className="animate-scan absolute inset-y-0 left-0 w-1/3"
        style={{
          background: 'linear-gradient(90deg, transparent, var(--phosphor)33, var(--phosphor)66, var(--phosphor)33, transparent)',
        }}
      />
      <p
        className="font-mono-display relative text-center text-xs font-bold tracking-[0.3em]"
        style={{ color: 'var(--phosphor)' }}
      >
        ANALYZING…
      </p>
    </div>
  )
}
