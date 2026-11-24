import VerdictStamp from './VerdictStamp'

const STANCE = {
  supports: { label: 'Supports', color: 'var(--phosphor)' },
  refutes: { label: 'Refutes', color: 'var(--alert)' },
  neutral: { label: 'Related', color: 'var(--paper-dim)' },
}

// Only http(s) links are clickable: the URLs come from the web, never trust them blindly.
function safeUrl(url) {
  try {
    const u = new URL(url)
    return u.protocol === 'http:' || u.protocol === 'https:' ? u.href : null
  } catch {
    return null
  }
}

function hostOf(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

function SectionLabel({ children }) {
  return (
    <p
      className="font-mono-display mb-2 text-[10px] font-bold tracking-widest uppercase"
      style={{ color: 'var(--paper-dim)' }}
    >
      {children}
    </p>
  )
}

function EvidenceItem({ item }) {
  const stance = STANCE[item.stance] || STANCE.neutral
  const href = safeUrl(item.url)

  return (
    <div
      className="flex flex-col gap-1.5 rounded border p-2.5 text-xs"
      style={{ borderColor: 'var(--ink-line)', background: 'var(--ink)' }}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span
          className="rounded px-2 py-0.5 text-[10px] font-bold tracking-wide uppercase"
          style={{ background: 'rgba(255, 255, 255, 0.08)', color: stance.color }}
        >
          {stance.label}
        </span>
        {item.source_type === 'fact_check' && (
          <span
            className="rounded px-2 py-0.5 text-[10px] font-bold tracking-wide uppercase"
            style={{ background: 'rgba(255, 255, 255, 0.08)', color: 'var(--paper-dim)' }}
          >
            Published fact-check
          </span>
        )}
      </div>
      <p className="leading-relaxed" style={{ color: 'var(--paper)' }}>
        “{item.quote}”
      </p>
      {href ? (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 break-all underline transition-opacity hover:opacity-80"
          style={{ color: 'var(--phosphor)' }}
        >
          {hostOf(item.url)}
          <span aria-hidden="true"> ↗</span>
        </a>
      ) : (
        <span style={{ color: 'var(--paper-dim)' }}>{hostOf(item.url)}</span>
      )}
    </div>
  )
}

export default function ClaimCard({ claim, index }) {
  const evidence = Array.isArray(claim.evidence) ? claim.evidence : []
  const factChecks = Array.isArray(claim.fact_checks) ? claim.fact_checks : []

  // Fact-checks already shown as verified quotes are not listed a second time.
  const quotedUrls = new Set(evidence.map((e) => e.url))
  const otherFactChecks = factChecks.filter((fc) => !quotedUrls.has(fc.url))

  const hasVerdict = claim.verdict !== 'unverifiable'
  const unbacked = hasVerdict && evidence.length === 0

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

      {evidence.length > 0 && (
        <div className="mt-3 border-t pt-3" style={{ borderColor: 'var(--ink-line)' }}>
          <SectionLabel>Evidence (quotes checked against the source)</SectionLabel>
          <div className="space-y-2">
            {evidence.map((item, i) => (
              <EvidenceItem key={i} item={item} />
            ))}
          </div>
        </div>
      )}

      {unbacked && (
        <div className="mt-3 border-t pt-2" style={{ borderColor: 'var(--ink-line)' }}>
          <p className="text-xs italic" style={{ color: 'var(--amber)' }}>
            No verified source quote backs this verdict. Treat it as an unchecked AI estimate.
          </p>
        </div>
      )}

      {otherFactChecks.length > 0 && (
        <div className="mt-3 border-t pt-3" style={{ borderColor: 'var(--ink-line)' }}>
          <SectionLabel>Other published fact-checks (not used for the verdict)</SectionLabel>
          <div className="space-y-2">
            {otherFactChecks.map((fc, i) => {
              const href = safeUrl(fc.url)
              return (
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
                        style={{ background: 'rgba(255, 255, 255, 0.08)', color: 'var(--phosphor)' }}
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
                  {href && (
                    <a
                      href={href}
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
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}