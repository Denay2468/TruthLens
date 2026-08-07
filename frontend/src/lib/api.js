// Base URL for the TruthLens backend. Set VITE_API_URL in a .env file for
// production (your Render deployment); defaults to local dev.
const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function handleResponse(res) {
  let body
  try {
    body = await res.json()
  } catch {
    throw new ApiError('The server sent back something unexpected.', res.status)
  }
  if (!res.ok) {
    throw new ApiError(body.detail || 'Something went wrong.', res.status)
  }
  return body
}

export async function scanUrl(url) {
  const res = await fetch(`${API_BASE}/api/scan/url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
  return handleResponse(res)
}

export async function scanText(text) {
  const res = await fetch(`${API_BASE}/api/scan/text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  return handleResponse(res)
}

export async function scanMedia(file) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${API_BASE}/api/scan/media`, {
    method: 'POST',
    body: formData,
  })
  return handleResponse(res)
}

export { ApiError }
