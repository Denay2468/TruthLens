const VERDICT_CONFIG = {
  true: {
    label: 'TRUE',
    color: 'var(--phosphor)',
    rotation: '-4deg',
  },
  false: {
    label: 'FALSE',
    color: 'var(--alert)',
    rotation: '3deg',
  },
  misleading: {
    label: 'MISLEADING',
    color: 'var(--amber)',
    rotation: '-2deg',
  },
  unverifiable: {
    label: 'UNVERIFIABLE',
    color: 'var(--paper-dim)',
    rotation: '2deg',
  },
}

export default function VerdictStamp({ verdict }) {
  const config = VERDICT_CONFIG[verdict] || VERDICT_CONFIG.unverifiable

  return (
    <div
      className="animate-stamp font-mono-display inline-block shrink-0 select-none whitespace-nowrap rounded-sm border-[3px] px-3 py-1 text-xs font-extrabold tracking-widest"
      style={{
        '--stamp-rot': config.rotation,
        color: config.color,
        borderColor: config.color,
        transform: `rotate(${config.rotation})`,
        textShadow: `0 0 12px ${config.color}55`,
      }}
    >
      {config.label}
    </div>
  )
}
