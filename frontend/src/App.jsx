import { useState } from 'react'
import ScanInput from './components/ScanInput'
import ScanResults from './components/ScanResults'
import { scanUrl, scanText, scanMedia, ApiError } from './lib/api'

const SAMPLE_MATCH = {
  source_summary: 'Demonstration of fact-check evidence integration.',
  overall_note: 'Cross-checked against published database and AI reasoning.',
  fact_check_status: 'ok',
  claims: [
    {
      text: 'Minum air rebusan bawang putih menyembuhkan infeksi virus secara instan.',
      verdict: 'false',
      reasoning: 'Klaim ini tidak memiliki dasar ilmiah medis dan telah dibantah oleh para ahli kesehatan.',
      fact_checks: [
        {
          publisher: 'TurnBackHoax Indonesia',
          rating: 'Salah / Hoaks',
          title: '[SALAH] Bawang Putih Rebus Dapat Menyembuhkan Virus Corona',
          url: 'https://turnbackhoax.id/2020/01/28/salah-bawang-putih-rebus-sembuhkan-virus-corona/',
          review_date: '2020-01-28',
        },
        {
          publisher: 'Kominfo RI',
          rating: 'Disinformasi',
          title: '[DISINFORMASI] Ramuan Rebusan Bawang Mengobati Virus',
          url: 'https://kominfo.go.id/content/detail/24021/disinformasi-ramuan-bawang-putih-sembuhkan-virus/0/laporan_isu_hoaks',
          review_date: '2020-01-29',
        },
      ],
    },
  ],
}

const SAMPLE_NO_MATCH = {
  source_summary: 'Scanned claim with no published fact-check match found.',
  overall_note: 'Verdict produced by AI estimation only.',
  fact_check_status: 'ok',
  claims: [
    {
      text: 'Studi lokal menunjukkan konsumsi buah naga membantu menurunkan gula darah.',
      verdict: 'unverifiable',
      reasoning: 'Terdapat penelitian awal pada hewan tetapi belum ada uji klinis berskala besar pada manusia.',
      fact_checks: [],
    },
  ],
}

const SAMPLE_UNAVAILABLE = {
  source_summary: 'System running with Google Fact Check API key unconfigured.',
  overall_note: 'AI evaluation remains available as fallback.',
  fact_check_status: 'unavailable',
  claims: [
    {
      text: 'Air mendidih pada suhu 100 derajat Celsius di permukaan laut.',
      verdict: 'true',
      reasoning: 'Sesuai dengan hukum fisika termodinamika standar pada tekanan 1 atmosfer.',
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
