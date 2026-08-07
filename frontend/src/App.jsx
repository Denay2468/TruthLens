import { useState } from 'react'
import ScanInput from './components/ScanInput'
import ScanResults from './components/ScanResults'
import { scanUrl, scanText, scanMedia, ApiError } from './lib/api'

export default function App() {
  const [isScanning, setIsScanning] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  async function handleScan({ type, payload }) {
    setIsScanning(true)
    setError(null)
    setResult(null)

    try {
      let data
      if (type === 'text') data = await scanText(payload)
      else if (type === 'url') data = await scanUrl(payload)
      else if (type === 'media') data = await scanMedia(payload)
      setResult(data)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Could not reach the scanner. Check that the backend is running.')
      }
    } finally {
      setIsScanning(false)
    }
  }

  return (
    <div className="mx-auto min-h-screen max-w-xl px-5 py-10">
      <header className="mb-10">
        <div className="mb-2 flex items-center gap-2">
          <span
            className="h-2 w-2 rounded-full"
            style={{ background: 'var(--phosphor)', boxShadow: '0 0 8px var(--phosphor)' }}
          />
          <span className="font-mono-display text-xs font-bold tracking-[0.3em]" style={{ color: 'var(--phosphor)' }}>
            MIL SCANNER
          </span>
        </div>
        <h1 className="font-mono-display text-3xl font-extrabold tracking-tight" style={{ color: 'var(--paper)' }}>
          TruthLens
        </h1>
        <p className="mt-2 text-sm leading-relaxed" style={{ color: 'var(--paper-dim)' }}>
          Paste a claim, a link, or upload a clip. TruthLens scans it and stamps a verdict on every claim it finds.
        </p>
      </header>

      <section className="mb-8">
        <ScanInput onScan={handleScan} isScanning={isScanning} />
      </section>

      <section>
        <p className="font-mono-display mb-3 text-xs font-bold tracking-widest" style={{ color: 'var(--paper-dim)' }}>
          RESULTS
        </p>
        <ScanResults isScanning={isScanning} error={error} result={result} />
      </section>

      <footer className="mt-16 text-center">
        <p className="text-xs" style={{ color: 'var(--paper-dim)' }}>
          TruthLens — a Media &amp; Information Literacy scanner
        </p>
      </footer>
    </div>
  )
}
