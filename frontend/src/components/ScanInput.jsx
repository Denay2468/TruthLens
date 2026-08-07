import { useState, useRef } from 'react'

const TABS = [
  { id: 'text', label: 'Text' },
  { id: 'url', label: 'URL' },
  { id: 'media', label: 'Media' },
]

export default function ScanInput({ onScan, isScanning }) {
  const [activeTab, setActiveTab] = useState('text')
  const [textValue, setTextValue] = useState('')
  const [urlValue, setUrlValue] = useState('')
  const [file, setFile] = useState(null)
  const fileInputRef = useRef(null)

  function handleSubmit(e) {
    e.preventDefault()
    if (activeTab === 'text' && textValue.trim()) {
      onScan({ type: 'text', payload: textValue.trim() })
    } else if (activeTab === 'url' && urlValue.trim()) {
      onScan({ type: 'url', payload: urlValue.trim() })
    } else if (activeTab === 'media' && file) {
      onScan({ type: 'media', payload: file })
    }
  }

  const canSubmit =
    (activeTab === 'text' && textValue.trim().length > 0) ||
    (activeTab === 'url' && urlValue.trim().length > 0) ||
    (activeTab === 'media' && file !== null)

  return (
    <form onSubmit={handleSubmit}>
      {/* Tab switcher */}
      <div
        className="mb-4 inline-flex gap-1 rounded-lg border p-1"
        style={{ borderColor: 'var(--ink-line)', background: 'var(--ink-raised)' }}
        role="tablist"
      >
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
            className="font-mono-display rounded-md px-4 py-2 text-xs font-bold tracking-wider transition-colors"
            style={{
              background: activeTab === tab.id ? 'var(--phosphor)' : 'transparent',
              color: activeTab === tab.id ? 'var(--ink)' : 'var(--paper-dim)',
            }}
          >
            {tab.label.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Input area */}
      <div
        className="rounded-lg border p-4"
        style={{ borderColor: 'var(--ink-line)', background: 'var(--ink-raised)' }}
      >
        {activeTab === 'text' && (
          <textarea
            value={textValue}
            onChange={(e) => setTextValue(e.target.value)}
            placeholder="Paste a claim, headline, or historical &quot;fact&quot; to check…"
            rows={5}
            className="w-full resize-none rounded-md border bg-transparent p-3 text-sm outline-none placeholder:text-[color:var(--paper-dim)]"
            style={{ borderColor: 'var(--ink-line)', color: 'var(--paper)' }}
          />
        )}

        {activeTab === 'url' && (
          <input
            type="url"
            value={urlValue}
            onChange={(e) => setUrlValue(e.target.value)}
            placeholder="https://example.com/article"
            className="w-full rounded-md border bg-transparent p-3 text-sm outline-none placeholder:text-[color:var(--paper-dim)]"
            style={{ borderColor: 'var(--ink-line)', color: 'var(--paper)' }}
          />
        )}

        {activeTab === 'media' && (
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".mp4,.mp3,.wav,.m4a,video/mp4,audio/mpeg,audio/wav,audio/mp4"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="hidden"
              id="media-input"
            />
            <label
              htmlFor="media-input"
              className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-md border border-dashed p-8 text-center transition-colors hover:border-[color:var(--phosphor)]"
              style={{ borderColor: 'var(--ink-line)' }}
            >
              <span className="font-mono-display text-xs font-bold tracking-wider" style={{ color: 'var(--paper-dim)' }}>
                {file ? file.name : 'CHOOSE AUDIO / VIDEO FILE'}
              </span>
              <span className="text-xs" style={{ color: 'var(--paper-dim)' }}>
                MP4, MP3, WAV, or M4A — up to 25MB
              </span>
            </label>
          </div>
        )}
      </div>

      <button
        type="submit"
        disabled={!canSubmit || isScanning}
        className="font-mono-display mt-4 w-full rounded-lg py-3 text-sm font-extrabold tracking-widest transition-opacity disabled:cursor-not-allowed disabled:opacity-40"
        style={{ background: 'var(--phosphor)', color: 'var(--ink)' }}
      >
        {isScanning ? 'SCANNING…' : 'SCAN'}
      </button>
    </form>
  )
}
