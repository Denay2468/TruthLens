import { useState } from 'react'
import ScanInput from './components/ScanInput'
import ScanResults from './components/ScanResults'
import { scanUrl, scanText, scanMedia, ApiError } from './lib/api'

// Demo data for the dev-only "Test UI" buttons. Same shape the real API returns.
const SAMPLE_MATCH = {
  source_summary: 'Demo: a claim refuted by published fact-checks.',
  overall_note: 'Checked 1 claim against sources: 1 false.',
  fact_check_status: 'ok',
  evidence_status: 'ok',
  claims: [
    {
      text: 'Minum air rebusan bawang putih menyembuhkan infeksi virus secara instan.',
      verdict: 'false',
      reasoning: 'Verified quotes from 2 sources contradict this claim, including 2 published fact-checks.',
      evidence: [
        {
          url: 'https://turnbackhoax.id/2020/01/28/salah-bawang-putih-rebus-sembuhkan-virus-corona/',
          title: 'TurnBackHoax Indonesia: [SALAH] Bawang Putih Rebus Dapat Menyembuhkan Virus Corona',
          quote: '[SALAH] Bawang Putih Rebus Dapat Menyembuhkan Virus Corona',
          stance: 'refutes',
          source_type: 'fact_check',
        },
        {
          url: 'https://kominfo.go.id/content/detail/24021/disinformasi-ramuan-bawang-putih-sembuhkan-virus/0/laporan_isu_hoaks',
          title: 'Kominfo RI: [DISINFORMASI] Ramuan Rebusan Bawang Mengobati Virus',
          quote: '[DISINFORMASI] Ramuan Rebusan Bawang Mengobati Virus',
          stance: 'refutes',
          source_type: 'fact_check',
        },
      ],
      fact_checks: [],
    },
  ],
}

const SAMPLE_NO_MATCH = {
  source_summary: 'Demo: a claim with no sources found.',
  overall_note: 'Checked 1 claim against sources: 1 unverifiable.',
  fact_check_status: 'ok',
  evidence_status: 'ok',
  claims: [
    {
      text: 'Studi lokal menunjukkan konsumsi buah naga membantu menurunkan gula darah.',
      verdict: 'unverifiable',
      reasoning: 'No sources were found for this claim, so it cannot be verified.',
      evidence: [],
      fact_checks: [],
    },
  ],
}

const SAMPLE_UNAVAILABLE = {
  source_summary: 'Demo: the evidence search failed.',
  overall_note:
    'Checked 1 claim against sources: 1 unverifiable. Some evidence searches failed, so some claims may be under-checked.',
  fact_check_status: 'unavailable',
  evidence_status: 'unavailable',
  claims: [
    {
      text: 'Air mendidih pada suhu 100 derajat Celsius di permukaan laut.',
      verdict: 'unverifiable',
      reasoning: 'The evidence search was unavailable just now, so this claim could not be checked. Try again.',
      evidence: [],
      fact_checks: [],
    },
  ],
}

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
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <p className="font-mono-display text-xs font-bold tracking-widest" style={{ color: 'var(--paper-dim)' }}>
            RESULTS
          </p>
          {(import.meta.env.DEV || import.meta.env.VITE_SHOW_TEST_UI === 'true') && (
          <div className="flex items-center gap-1.5 text-[10px]">
            <span style={{ color: 'var(--paper-dim)' }}>Test UI:</span>
            <button
              type="button"
              onClick={() => { setError(null); setResult(SAMPLE_MATCH); }}
              className="rounded border px-2 py-0.5 transition-colors hover:border-[color:var(--phosphor)]"
              style={{ borderColor: 'var(--ink-line)', color: 'var(--paper)', background: 'var(--ink-raised)' }}
            >
              Match
            </button>
            <button
              type="button"
              onClick={() => { setError(null); setResult(SAMPLE_NO_MATCH); }}
              className="rounded border px-2 py-0.5 transition-colors hover:border-[color:var(--phosphor)]"
              style={{ borderColor: 'var(--ink-line)', color: 'var(--paper)', background: 'var(--ink-raised)' }}
            >
              No Match
            </button>
            <button
              type="button"
              onClick={() => { setError(null); setResult(SAMPLE_UNAVAILABLE); }}
              className="rounded border px-2 py-0.5 transition-colors hover:border-[color:var(--phosphor)]"
              style={{ borderColor: 'var(--ink-line)', color: 'var(--paper)', background: 'var(--ink-raised)' }}
            >
              Unavailable
            </button>
          </div>
          )}
        </div>
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