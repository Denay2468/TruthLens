# TruthLens

## How it works

1. **Text** — pasted text goes straight to Groq's LLM with a fact-checking
   prompt; returns claims with verdicts and reasoning.
2. **URL** — the page is scraped (httpx + BeautifulSoup) for its main
   readable text, then fact-checked the same way. Works best on static
   article pages (Wikipedia, news sites); JS-heavy pages like YouTube won't
   scrape their real content since we don't render JavaScript.
3. **Media** — the uploaded audio/video is transcribed via Groq's hosted
   Whisper API, then the transcript is fact-checked the same way as text.
