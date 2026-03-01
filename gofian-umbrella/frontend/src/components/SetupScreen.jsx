import React, { useState, useEffect, useCallback } from 'react'
import CitySearch from './CitySearch'

/**
 * SetupScreen — GOFIAN CREATIVE Onboarding v0.4.0
 *
 * Philosophy: ZERO friction. One tap or one search → BAM → your weather.
 * v0.4: Real API-backed city search replaces hardcoded WORLD_CITIES.
 * GPS now uses reverse geocoding for accurate city name.
 */

export default function SetupScreen({ onComplete }) {
  const [phase, setPhase] = useState('intro')
  const [gpsStatus, setGpsStatus] = useState(null)
  const [transitioning, setTransitioning] = useState(false)

  // Entrance animation
  useEffect(() => {
    const t = setTimeout(() => setPhase('locate'), 800)
    return () => clearTimeout(t)
  }, [])

  // Save to localStorage and trigger transition
  const saveAndTransition = useCallback((city) => {
    localStorage.setItem('uos_location', JSON.stringify({
      name: city.name,
      country: city.country || '',
      lat: city.lat || city.latitude,
      lon: city.lon || city.longitude,
      street: city.street || '',
      neighborhood: city.neighborhood || '',
      isGPS: city.isGPS || false,
      savedAt: new Date().toISOString(),
    }))

    // Also save to backend (best effort)
    fetch('/api/v1/locations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: city.name,
        latitude: city.lat || city.latitude,
        longitude: city.lon || city.longitude,
        city: city.name,
        country: city.country || '',
        is_home: true,
      }),
    }).catch(() => {})

    // Transition animation
    setTransitioning(true)
    setTimeout(() => {
      onComplete({
        name: city.name,
        country: city.country || '',
        latitude: city.lat || city.latitude,
        longitude: city.lon || city.longitude,
        isGPS: city.isGPS || false,
      })
    }, 600)
  }, [onComplete])

  // GPS locate with reverse geocoding
  const handleGPS = useCallback(() => {
    if (!navigator.geolocation) {
      setGpsStatus('error')
      return
    }
    setGpsStatus('loading')
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude
        const lon = pos.coords.longitude
        setGpsStatus('success')

        // Reverse geocode for city name
        let name = 'My Location'
        let country = ''
        let street = ''
        let neighborhood = ''
        try {
          const res = await fetch(`/api/v1/geocode/reverse?lat=${lat}&lon=${lon}`)
          const data = await res.json()
          const geo = data.data || {}
          name = geo.city || 'My Location'
          country = geo.country || ''
          street = geo.street || ''
          neighborhood = geo.neighborhood || ''
        } catch { /* keep defaults */ }

        saveAndTransition({ name, country, lat, lon, street, neighborhood, isGPS: true })
      },
      (err) => {
        console.warn('GPS error:', err)
        setGpsStatus(err.code === 1 ? 'denied' : 'error')
      },
      { enableHighAccuracy: true, timeout: 10000 }
    )
  }, [saveAndTransition])

  // City selected from CitySearch API
  const handleCitySelect = useCallback((city) => {
    saveAndTransition({
      name: city.name,
      country: city.country || '',
      lat: city.lat,
      lon: city.lon,
    })
  }, [saveAndTransition])

  return (
    <div className={`setup-screen ${transitioning ? 'setup-exit' : ''}`}>
      <div className="setup-atmosphere" />

      <div className="setup-container">
        {phase === 'intro' && (
          <div className="setup-intro">
            <div className="setup-logo-pulse">🌦️</div>
          </div>
        )}

        {phase === 'locate' && (
          <div className="setup-locate animate-setup-enter">
            <h1 className="setup-title">Where are you?</h1>
            <p className="setup-subtitle">One tap. Your weather. Instantly.</p>

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
              <p className="setup-gps-hint">Location access denied. Search your city below.</p>
            )}
            {gpsStatus === 'error' && (
              <p className="setup-gps-hint">Could not detect location. Search below.</p>
            )}

            <div className="setup-divider">
              <span>or search</span>
            </div>

            {/* v0.4: Real API-backed city search */}
            <div className="setup-search-wrap">
              <CitySearch onSelect={handleCitySelect} placeholder="Type a city name..." />
            </div>

            <p className="setup-footer">Powered by GOFIAN AI</p>
          </div>
        )}
      </div>
    </div>
  )
}
