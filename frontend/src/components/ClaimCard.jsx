import VerdictStamp from './VerdictStamp'

export default function ClaimCard({ claim, index, factCheckStatus }) {
  const factChecks = Array.isArray(claim.fact_checks) ? claim.fact_checks : []
  const hasFactChecks = factChecks.length > 0
  const isOkStatus = factCheckStatus === 'ok'

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

      {/* Published Fact-Checks */}
      {hasFactChecks && (
        <div className="mt-3 border-t pt-3" style={{ borderColor: 'var(--ink-line)' }}>
          <p
            className="font-mono-display mb-2 text-[10px] font-bold tracking-widest uppercase"
            style={{ color: 'var(--paper-dim)' }}
          >
            Published Fact-Checks
          </p>
          <div className="space-y-2">
            {factChecks.map((fc, i) => (
              <div
                key={i}
                className="flex flex-col gap-1 rounded border p-2.5 text-xs"
                style={{ borderColor: 'var(--ink-line)', background: 'var(--ink)' }}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-semibold" style={{ color: 'var(--paper)' }}>
                    {fc.publisher || 'Unknown Publisher'}
                  </span>
                  {fc.rating && (
                    <span
                      className="rounded px-2 py-0.5 text-[10px] font-bold tracking-wide uppercase"
                      style={{
                        background: 'rgba(255, 255, 255, 0.08)',
                        color: 'var(--phosphor)',
                      }}
                    >
                      Rating: {fc.rating}
                    </span>
                  )}
                </div>
                {fc.title && (
                  <p className="line-clamp-2 text-xs" style={{ color: 'var(--paper-dim)' }}>
                    {fc.title}
                  </p>
                )}
                {fc.url && (
                  <a
                    href={fc.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1 inline-flex items-center gap-1 text-xs break-all underline transition-opacity hover:opacity-80"
                    style={{ color: 'var(--phosphor)' }}
                  >
                    View review on {fc.publisher || 'source'}
                    <span aria-hidden="true"> ↗</span>
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State: only show if backend explicitly ok but no published matches found */}
      {!hasFactChecks && isOkStatus && (
        <div className="mt-3 border-t pt-2" style={{ borderColor: 'var(--ink-line)' }}>
          <p className="text-xs italic" style={{ color: 'var(--paper-dim)' }}>
            No published fact-check found. This verdict is an AI estimate only.
          </p>
        </div>
      )}
    </div>
  )
}
