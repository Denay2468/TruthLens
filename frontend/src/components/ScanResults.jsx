import ClaimCard from './ClaimCard'
import ScanBeam from './ScanBeam'

export default function ScanResults({ isScanning, error, result }) {
  if (isScanning) {
    return <ScanBeam />
  }

  if (error) {
    return (
      <div
        className="rounded-lg border p-4"
        style={{ borderColor: 'var(--alert)', background: 'var(--ink-raised)' }}
      >
        <p className="font-mono-display mb-1 text-xs font-bold tracking-widest" style={{ color: 'var(--alert)' }}>
          SCAN FAILED
        </p>
        <p className="text-sm" style={{ color: 'var(--paper)' }}>
          {error}
        </p>
      </div>
    )
  }

  if (!result) {
    return (
      <div
        className="rounded-lg border border-dashed p-8 text-center"
        style={{ borderColor: 'var(--ink-line)' }}
      >
        <p className="text-sm" style={{ color: 'var(--paper-dim)' }}>
          Results will appear here once you run a scan.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {result.source_summary && (
        <p className="text-xs italic" style={{ color: 'var(--paper-dim)' }}>
          {result.source_summary}
        </p>
      )}

      {result.claims.length === 0 ? (
        <div
          className="rounded-lg border p-4"
          style={{ borderColor: 'var(--ink-line)', background: 'var(--ink-raised)' }}
        >
          <p className="text-sm" style={{ color: 'var(--paper)' }}>
            No checkable factual claims were found.
          </p>
        </div>
      ) : (
        result.claims.map((claim, i) => <ClaimCard key={i} claim={claim} index={i} />)
      )}

      {result.overall_note && (
        <div
          className="rounded-lg border-l-4 p-3"
          style={{ borderColor: 'var(--phosphor)', background: 'var(--ink-raised)' }}
        >
          <p className="text-xs" style={{ color: 'var(--paper)' }}>
            {result.overall_note}
          </p>
        </div>
      )}

      <p className="pt-2 text-xs leading-relaxed" style={{ color: 'var(--paper-dim)' }}>
        This is an AI-generated assessment. It can be wrong and is not proof or legal evidence.
        Check the original sources before you rely on it.
      </p>
    </div>
  )
}
