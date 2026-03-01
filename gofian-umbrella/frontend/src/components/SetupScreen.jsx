import React, { useState, useEffect, useCallback, useRef } from 'react'

/**
 * SetupScreen — GOFIAN CREATIVE Onboarding v0.3.0
 *
 * Philosophy: ZERO friction. One tap or one search → BAM → your weather.
 * The setup IS the experience. Beautiful, atmospheric, immediate.
 *
 * Flow:
 *   1. Full-viewport atmospheric intro with pulsing 📍
 *   2. Two paths: GPS auto-detect OR city search
 *   3. Animated transition → weather view
 *   4. localStorage saves choice → never show setup again
 */

// ============================================================
// Major world cities for instant search (no API needed)
// ============================================================
const WORLD_CITIES = [
  { name: 'Paris', country: 'FR', lat: 48.8566, lon: 2.3522 },
  { name: 'London', country: 'GB', lat: 51.5074, lon: -0.1278 },
  { name: 'New York', country: 'US', lat: 40.7128, lon: -74.0060 },
  { name: 'Tokyo', country: 'JP', lat: 35.6762, lon: 139.6503 },
  { name: 'Sydney', country: 'AU', lat: -33.8688, lon: 151.2093 },
  { name: 'Berlin', country: 'DE', lat: 52.5200, lon: 13.4050 },
  { name: 'Madrid', country: 'ES', lat: 40.4168, lon: -3.7038 },
  { name: 'Rome', country: 'IT', lat: 41.9028, lon: 12.4964 },
  { name: 'Amsterdam', country: 'NL', lat: 52.3676, lon: 4.9041 },
  { name: 'Dubai', country: 'AE', lat: 25.2048, lon: 55.2708 },
  { name: 'Singapore', country: 'SG', lat: 1.3521, lon: 103.8198 },
  { name: 'Hong Kong', country: 'HK', lat: 22.3193, lon: 114.1694 },
  { name: 'Seoul', country: 'KR', lat: 37.5665, lon: 126.9780 },
  { name: 'Mumbai', country: 'IN', lat: 19.0760, lon: 72.8777 },
  { name: 'São Paulo', country: 'BR', lat: -23.5505, lon: -46.6333 },
  { name: 'Mexico City', country: 'MX', lat: 19.4326, lon: -99.1332 },
  { name: 'Cairo', country: 'EG', lat: 30.0444, lon: 31.2357 },
  { name: 'Istanbul', country: 'TR', lat: 41.0082, lon: 28.9784 },
  { name: 'Moscow', country: 'RU', lat: 55.7558, lon: 37.6173 },
  { name: 'Bangkok', country: 'TH', lat: 13.7563, lon: 100.5018 },
  { name: 'Limassol', country: 'CY', lat: 34.6841, lon: 33.0379 },
  { name: 'Brussels', country: 'BE', lat: 50.8503, lon: 4.3517 },
  { name: 'Lisbon', country: 'PT', lat: 38.7223, lon: -9.1393 },
  { name: 'Vienna', country: 'AT', lat: 48.2082, lon: 16.3738 },
  { name: 'Stockholm', country: 'SE', lat: 59.3293, lon: 18.0686 },
  { name: 'Oslo', country: 'NO', lat: 59.9139, lon: 10.7522 },
  { name: 'Copenhagen', country: 'DK', lat: 55.6761, lon: 12.5683 },
  { name: 'Athens', country: 'GR', lat: 37.9838, lon: 23.7275 },
  { name: 'Prague', country: 'CZ', lat: 50.0755, lon: 14.4378 },
  { name: 'Warsaw', country: 'PL', lat: 52.2297, lon: 21.0122 },
  { name: 'Zurich', country: 'CH', lat: 47.3769, lon: 8.5417 },
  { name: 'Geneva', country: 'CH', lat: 46.2044, lon: 6.1432 },
  { name: 'Los Angeles', country: 'US', lat: 34.0522, lon: -118.2437 },
  { name: 'San Francisco', country: 'US', lat: 37.7749, lon: -122.4194 },
  { name: 'Chicago', country: 'US', lat: 41.8781, lon: -87.6298 },
  { name: 'Miami', country: 'US', lat: 25.7617, lon: -80.1918 },
  { name: 'Toronto', country: 'CA', lat: 43.6532, lon: -79.3832 },
  { name: 'Vancouver', country: 'CA', lat: 49.2827, lon: -123.1207 },
  { name: 'Montréal', country: 'CA', lat: 45.5017, lon: -73.5673 },
  { name: 'Buenos Aires', country: 'AR', lat: -34.6037, lon: -58.3816 },
  { name: 'Cape Town', country: 'ZA', lat: -33.9249, lon: 18.4241 },
  { name: 'Nairobi', country: 'KE', lat: -1.2921, lon: 36.8219 },
  { name: 'Lagos', country: 'NG', lat: 6.5244, lon: 3.3792 },
  { name: 'Marrakech', country: 'MA', lat: 31.6295, lon: -7.9811 },
  { name: 'Reykjavik', country: 'IS', lat: 64.1466, lon: -21.9426 },
  { name: 'Helsinki', country: 'FI', lat: 60.1699, lon: 24.9384 },
  { name: 'Dublin', country: 'IE', lat: 53.3498, lon: -6.2603 },
  { name: 'Edinburgh', country: 'GB', lat: 55.9533, lon: -3.1883 },
  { name: 'Barcelona', country: 'ES', lat: 41.3874, lon: 2.1686 },
  { name: 'Nice', country: 'FR', lat: 43.7102, lon: 7.2620 },
  { name: 'Lyon', country: 'FR', lat: 45.7640, lon: 4.8357 },
  { name: 'Marseille', country: 'FR', lat: 43.2965, lon: 5.3698 },
]

const FLAGS = {
  FR: '🇫🇷', GB: '🇬🇧', US: '🇺🇸', JP: '🇯🇵', AU: '🇦🇺',
  DE: '🇩🇪', ES: '🇪🇸', IT: '🇮🇹', NL: '🇳🇱', AE: '🇦🇪',
  SG: '🇸🇬', HK: '🇭🇰', KR: '🇰🇷', IN: '🇮🇳', BR: '🇧🇷',
  MX: '🇲🇽', EG: '🇪🇬', TR: '🇹🇷', RU: '🇷🇺', TH: '🇹🇭',
  CY: '🇨🇾', BE: '🇧🇪', PT: '🇵🇹', AT: '🇦🇹', SE: '🇸🇪',
  NO: '🇳🇴', DK: '🇩🇰', GR: '🇬🇷', CZ: '🇨🇿', PL: '🇵🇱',
  CH: '🇨🇭', CA: '🇨🇦', AR: '🇦🇷', ZA: '🇿🇦', KE: '🇰🇪',
  NG: '🇳🇬', MA: '🇲🇦', IS: '🇮🇸', FI: '🇫🇮', IE: '🇮🇪',
}

export default function SetupScreen({ onComplete }) {
  const [phase, setPhase] = useState('intro') // intro → locate → searching → done
  const [gpsStatus, setGpsStatus] = useState(null) // null, 'loading', 'success', 'denied', 'error'
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [selectedCity, setSelectedCity] = useState(null)
  const [transitioning, setTransitioning] = useState(false)
  const inputRef = useRef(null)

  // Entrance animation
  useEffect(() => {
    const t = setTimeout(() => setPhase('locate'), 800)
    return () => clearTimeout(t)
  }, [])

  // Search cities
  useEffect(() => {
    if (!searchQuery || searchQuery.length < 1) {
      setSearchResults([])
      return
    }
    const q = searchQuery.toLowerCase()
    const matches = WORLD_CITIES.filter(c =>
      c.name.toLowerCase().includes(q) ||
      c.country.toLowerCase().includes(q)
    ).slice(0, 6)
    setSearchResults(matches)
  }, [searchQuery])

  // GPS locate
  const handleGPS = useCallback(() => {
    if (!navigator.geolocation) {
      setGpsStatus('error')
      return
    }
    setGpsStatus('loading')
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGpsStatus('success')
        const loc = {
          name: 'My Location',
          country: '',
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          isGPS: true,
        }
        setSelectedCity(loc)
        // Save + transition
        saveAndTransition(loc)
      },
      (err) => {
        console.warn('GPS error:', err)
        setGpsStatus(err.code === 1 ? 'denied' : 'error')
      },
      { enableHighAccuracy: true, timeout: 10000 }
    )
  }, [])

  // Select a city from search
  const handleCitySelect = useCallback((city) => {
    setSelectedCity(city)
    setSearchQuery('')
    setSearchResults([])
    saveAndTransition(city)
  }, [])

  // Save to localStorage and trigger transition
  const saveAndTransition = useCallback((city) => {
    // Save to localStorage
    localStorage.setItem('uos_location', JSON.stringify({
      name: city.name,
      country: city.country || '',
      lat: city.lat,
      lon: city.lon,
      isGPS: city.isGPS || false,
      savedAt: new Date().toISOString(),
    }))

    // Also save to backend as a new location
    fetch('/api/v1/locations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: city.name,
        latitude: city.lat,
        longitude: city.lon,
        city: city.name,
        country: city.country || '',
        is_home: true,
      }),
    }).catch(() => {}) // Best effort

    // Transition animation
    setTransitioning(true)
    setTimeout(() => {
      onComplete({
        name: city.name,
        country: city.country || '',
        latitude: city.lat,
        longitude: city.lon,
        isGPS: city.isGPS || false,
      })
    }, 600)
  }, [onComplete])

  return (
    <div className={`setup-screen ${transitioning ? 'setup-exit' : ''}`}>
      {/* Atmospheric background */}
      <div className="setup-atmosphere" />

      <div className="setup-container">
        {/* Phase 1: Intro pulse */}
        {phase === 'intro' && (
          <div className="setup-intro">
            <div className="setup-logo-pulse">🌦️</div>
          </div>
        )}

        {/* Phase 2: Location selection */}
        {phase === 'locate' && (
          <div className="setup-locate animate-setup-enter">
            <h1 className="setup-title">Where are you?</h1>
            <p className="setup-subtitle">One tap. Your weather. Instantly.</p>

            {/* GPS Button — The star of the show */}
            <button
              className={`setup-gps-btn ${gpsStatus === 'loading' ? 'setup-gps-loading' : ''} ${gpsStatus === 'success' ? 'setup-gps-success' : ''}`}
              onClick={handleGPS}
              disabled={gpsStatus === 'loading'}
            >
              {gpsStatus === 'loading' ? (
                <span className="setup-gps-spinner">📡</span>
              ) : gpsStatus === 'success' ? (
                <span>✅ Located!</span>
              ) : (
                <>
                  <span className="setup-gps-icon">🎯</span>
                  <span>Use my location</span>
                </>
              )}
            </button>

            {gpsStatus === 'denied' && (
              <p className="setup-gps-hint">
                Location access denied. Search your city below.
              </p>
            )}
            {gpsStatus === 'error' && (
              <p className="setup-gps-hint">
                Could not detect location. Search below.
              </p>
            )}

            {/* Divider */}
            <div className="setup-divider">
              <span>or search</span>
            </div>

            {/* City Search */}
            <div className="setup-search-wrap">
              <input
                ref={inputRef}
                type="text"
                className="setup-search-input"
                placeholder="Type a city name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                autoComplete="off"
                autoCorrect="off"
                spellCheck="false"
              />

              {/* Search Results */}
              {searchResults.length > 0 && (
                <div className="setup-search-results">
                  {searchResults.map((city, i) => (
                    <button
                      key={`${city.name}-${city.country}`}
                      className="setup-search-item"
                      onClick={() => handleCitySelect(city)}
                      style={{ animationDelay: `${i * 50}ms` }}
                    >
                      <span className="setup-search-flag">
                        {FLAGS[city.country] || '🌍'}
                      </span>
                      <span className="setup-search-name">{city.name}</span>
                      <span className="setup-search-country">{city.country}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Footer hint */}
            <p className="setup-footer">
              Powered by GOFIAN AI
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
