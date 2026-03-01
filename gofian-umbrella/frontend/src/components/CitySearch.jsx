/**
 * GOFIAN UoS v0.4.0 — CitySearch Component
 * Real API-backed city search with debounce.
 * Uses /api/v1/geocode/search endpoint.
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import { countryToFlag } from '../utils/countryFlag'

export default function CitySearch({ onSelect, placeholder = 'Type a city name...', autoFocus = false }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)
  const debounceRef = useRef(null)

  // Debounced search effect
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)

    const trimmed = query.trim()
    if (trimmed.length < 2) {
      setResults([])
      setLoading(false)
      setError(null)
      return
    }

    setLoading(true)
    setError(null)

    debounceRef.current = setTimeout(async () => {
      try {
        const res = await fetch(`/api/v1/geocode/search?q=${encodeURIComponent(trimmed)}&limit=6`)
        if (!res.ok) throw new Error('Search failed')
        const data = await res.json()
        setResults(data.data || [])
        setError(null)
      } catch (e) {
        setResults([])
        setError('Search unavailable')
      } finally {
        setLoading(false)
      }
    }, 300)

    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [query])

  // Auto-focus
  useEffect(() => {
    if (autoFocus && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [autoFocus])

  const handleSelect = useCallback((city) => {
    setQuery('')
    setResults([])
    onSelect?.(city)
  }, [onSelect])

  return (
    <div className="city-search">
      <input
        ref={inputRef}
        type="text"
        className="city-search__input"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        autoComplete="off"
        autoCorrect="off"
        spellCheck={false}
        aria-label="Search for a city"
      />

      {query.length >= 2 && (
        <div className="city-search__dropdown">
          {loading && (
            <div className="city-search__status">Searching...</div>
          )}
          {error && (
            <div className="city-search__status city-search__error">{error}</div>
          )}
          {!loading && !error && results.length === 0 && query.length >= 2 && (
            <div className="city-search__status">No cities found</div>
          )}
          {results.map((city, i) => (
            <button
              key={`${city.name}-${city.country}-${i}`}
              className="city-search__result"
              onClick={() => handleSelect(city)}
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <span className="city-search__flag">{countryToFlag(city.country)}</span>
              <span className="city-search__name">
                {city.name}
                {city.state && <span className="city-search__state">, {city.state}</span>}
              </span>
              <span className="city-search__country">{city.country}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
