import VerdictStamp from './VerdictStamp'

export default function ClaimCard({ claim, index }) {
  return (
    <div
      className="animate-card-in rounded-lg border p-4"
      style={{
        borderColor: 'var(--ink-line)',
        background: 'var(--ink-raised)',
        animationDelay: `${index * 80}ms`,
      }}
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <p className="text-sm leading-relaxed" style={{ color: 'var(--paper)' }}>
          {claim.text}
        </p>
        <VerdictStamp verdict={claim.verdict} />
      </div>
      <p className="text-xs leading-relaxed" style={{ color: 'var(--paper-dim)' }}>
        {claim.reasoning}
      </p>
    </div>
  )
}
