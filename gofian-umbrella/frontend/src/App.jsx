import React, { useState, useEffect, useCallback, useMemo } from 'react'
import WeatherIcon from './components/WeatherIcon'
import ExplainOverlay from './components/ExplainOverlay'
import LocationSelector from './components/LocationSelector'
import SetupScreen from './components/SetupScreen'
import { useDecision, useStreak, useLocations, submitFeedback } from './hooks/useDecision'

/**
 * UoS v0.3.0 — Umbrella or Sunglasses
 * "One glance. One decision."
 *
 * GOFIAN CREATIVE v0.3: Setup → BAM → Your Weather
 * Zero-friction onboarding. GPS or city search. localStorage memory.
 * The setup IS the experience.
 */

// ============================================================
// Atmosphere: Dynamic background gradient (Council Phase B1)
// The weather IS the interface. Background shifts with weather+time.
// ============================================================

const ATMOSPHERE_THEMES = {
  // Time-of-day base gradients (Council Phases B1, B4)
  dawn:    { top: '#1a0a2e', mid: '#4a1942', bottom: '#e8896b' },
  morning: { top: '#1a365d', mid: '#2b6cb0', bottom: '#f6e05e' },
  noon:    { top: '#1e3a5f', mid: '#2b6cb0', bottom: '#4299e1' },
  afternoon: { top: '#1a365d', mid: '#2c5282', bottom: '#4a5568' },
  golden:  { top: '#451a03', mid: '#92400e', bottom: '#f59e0b' },
  evening: { top: '#1a1a2e', mid: '#16213e', bottom: '#0f3460' },
  night:   { top: '#020617', mid: '#0a0e1a', bottom: '#111827' },
}

const WEATHER_OVERLAYS = {
  umbrella: 'rain',
  sunglasses: null,
  danger: 'danger',
  wind: null,
  cold: null,
  heat: null,
  clear: null,
  sunrise: 'golden',
  sunset: 'golden',
}

function getTimeOfDay(ephemeris) {
  if (!ephemeris) return 'noon'
  const elev = ephemeris.sun_elevation || 0
  const isGolden = ephemeris.is_golden_hour

  if (isGolden && elev > 0 && elev < 10) {
    // Determine morning or evening golden hour
    if (ephemeris.sunrise && ephemeris.sunset) {
      const now = new Date()
      const localH = now.getUTCHours() + (ephemeris.longitude || 0) / 15
      const sunriseH = parseInt(ephemeris.sunrise.split(':')[0])
      const sunsetH = parseInt(ephemeris.sunset.split(':')[0])
      return Math.abs(localH - sunriseH) < Math.abs(localH - sunsetH) ? 'dawn' : 'golden'
    }
    return 'golden'
  }
  if (elev <= -6) return 'night'
  if (elev <= 0) return 'evening'
  if (elev > 0 && elev < 15) return 'morning'
  if (elev > 50) return 'noon'
  return 'afternoon'
}

function AtmosphericBackground({ icon, ephemeris }) {
  const timeOfDay = getTimeOfDay(ephemeris)
  const theme = ATMOSPHERE_THEMES[timeOfDay] || ATMOSPHERE_THEMES.noon
  const overlay = WEATHER_OVERLAYS[icon] || (timeOfDay === 'night' ? 'night' : null)

  const overlayClass = overlay ? `atmosphere--${overlay}` : ''

  return (
    <div
      className={`atmosphere ${overlayClass}`}
      style={{
        '--atmo-top': theme.top,
        '--atmo-mid': theme.mid,
        '--atmo-bottom': theme.bottom,
      }}
    />
  )
}

// ============================================================
// Rain Particles (Council Phase B2)
// CSS-only rain streaks — lightweight, no Canvas needed
// ============================================================

function RainLayer({ intensity }) {
  const drops = useMemo(() => {
    const count = intensity === 'intense' ? 80 : intensity === 'moderate' ? 40 : 20
    return Array.from({ length: count }, (_, i) => ({
      x: Math.random() * 100,
      speed: 0.4 + Math.random() * 0.6,
      delay: Math.random() * 2,
      size: ['light', 'medium', 'heavy'][Math.floor(Math.random() * 3)],
    }))
  }, [intensity])

  return (
    <div className="rain-layer">
      {drops.map((d, i) => (
        <div
          key={i}
          className={`rain-drop rain-drop--${d.size}`}
          style={{
            '--drop-x': `${d.x}%`,
            '--drop-speed': `${d.speed}s`,
            '--drop-delay': `${d.delay}s`,
          }}
        />
      ))}
    </div>
  )
}

// ============================================================
// History Strip (Council Phase C2)
// 7 colored dots for last 7 days of decisions
// ============================================================

function HistoryStrip({ decisions }) {
  if (!decisions || decisions.length === 0) return null

  const ICON_TO_COLOR = {
    sunglasses: 'sun', umbrella: 'rain', wind: 'wind',
    cold: 'cold', heat: 'heat', danger: 'danger', clear: 'clear',
    sunrise: 'sun', sunset: 'sun',
  }

  const last7 = decisions.slice(0, 7)

  return (
    <div className="history-strip">
      {last7.map((d, i) => (
        <div
          key={i}
          className={`history-dot history-dot--${ICON_TO_COLOR[d.primary_icon] || 'clear'}`}
          title={d.primary_icon}
        />
      ))}
    </div>
  )
}


// ============================================================
// Main App
// ============================================================

export default function App() {
  // v0.3: Setup flow — check localStorage for saved location
  const [needsSetup, setNeedsSetup] = useState(() => {
    const saved = localStorage.getItem('uos_location')
    return !saved
  })

  const [selectedLocation, setSelectedLocation] = useState(() => {
    const saved = localStorage.getItem('uos_location')
    if (saved) {
      try {
        const loc = JSON.parse(saved)
        return { name: loc.name, country: loc.country, latitude: loc.lat, longitude: loc.lon }
      } catch { return null }
    }
    return null
  })

  const [showLocations, setShowLocations] = useState(false)
  const [showExplain, setShowExplain] = useState(false)
  const [toast, setToast] = useState(null)
  const [celebrating, setCelebrating] = useState(false)
  const [entered, setEntered] = useState(false)
  const [recentDecisions, setRecentDecisions] = useState([])

  const { locations } = useLocations()

  // Compute lat/lon BEFORE hooks that need them (hooks must be unconditional)
  const lat = selectedLocation?.latitude ?? 48.8566
  const lon = selectedLocation?.longitude ?? 2.3522

  // ALL hooks must be called unconditionally (React rules of hooks)
  const { decision, weather, ephemeris, loading, error, refresh } = useDecision(lat, lon)
  const { streak, checkIn } = useStreak()

  // v0.3: Setup complete callback — comes from SetupScreen
  const handleSetupComplete = useCallback((loc) => {
    setSelectedLocation(loc)
    setNeedsSetup(false)
  }, [])

  // Show toast (must be before handleFeedback which uses it)
  const showToast = useCallback((msg) => {
    setToast(msg)
    setTimeout(() => setToast(null), 2500)
  }, [])

  // Feedback with celebration (Council Phase C4)
  const handleFeedback = useCallback(async (fb) => {
    if (!decision?.decision_id) return
    await submitFeedback(decision.decision_id, fb)
    if (fb === 'correct') {
      setCelebrating(true)
      setTimeout(() => setCelebrating(false), 600)
    }
    showToast(fb === 'correct' ? '👍' : '👎')
  }, [decision, showToast])

  // Auto check-in on first load (skip during setup)
  useEffect(() => {
    if (!needsSetup && selectedLocation && decision && !loading) {
      checkIn()
    }
  }, [needsSetup, selectedLocation, decision, loading]) // eslint-disable-line react-hooks/exhaustive-deps

  // Entrance animation trigger (Council Phase B3)
  useEffect(() => {
    if (!needsSetup && selectedLocation && decision && !loading) {
      setEntered(false)
      const t = setTimeout(() => setEntered(true), 50)
      return () => clearTimeout(t)
    }
  }, [needsSetup, selectedLocation, decision, loading])

  // Fetch recent decisions for history strip
  useEffect(() => {
    if (!needsSetup && selectedLocation && decision) {
      fetch('/api/v1/decisions?limit=7')
        .then(r => r.json())
        .then(d => setRecentDecisions(d.data || []))
        .catch(() => {})
    }
  }, [needsSetup, selectedLocation, decision])

  // v0.3: If Setup is needed, show SetupScreen (after ALL hooks)
  if (needsSetup || !selectedLocation) {
    return <SetupScreen onComplete={handleSetupComplete} />
  }

  // Loading state
  if (loading) {
    return (
      <>
        <div className="atmosphere" />
        <div className="loading-screen">🌦️</div>
      </>
    )
  }

  // Error state
  if (error) {
    return (
      <>
        <div className="atmosphere" />
        <div className="app-container">
          <div className="main-icon-area">
            <span style={{ fontSize: '80px' }}>⚠️</span>
            <p style={{ color: 'var(--text-dim)', fontSize: '14px', marginTop: '16px' }}>
              {error}
            </p>
            <button
              onClick={refresh}
              style={{
                marginTop: '16px',
                background: 'var(--bg-card)',
                border: '1px solid var(--accent-sun)',
                color: 'var(--accent-sun)',
                borderRadius: '20px',
                padding: '8px 24px',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              ↻
            </button>
          </div>
        </div>
      </>
    )
  }

  const FLAGS = {
    FR: '🇫🇷', CY: '🇨🇾', US: '🇺🇸', JP: '🇯🇵', AU: '🇦🇺',
    GB: '🇬🇧', DE: '🇩🇪', ES: '🇪🇸', IT: '🇮🇹', BR: '🇧🇷',
  }

  const primaryIcon = decision?.primary_icon || 'sunglasses'
  const isRaining = primaryIcon === 'umbrella'
  const isDemoData = weather?.source === 'demo'

  // Glow color class by icon type (Council Phase A4)
  const glowColorClass = {
    umbrella: 'glow-rain',
    cold: 'glow-cold',
    heat: 'glow-heat',
    wind: 'glow-wind',
    danger: 'glow-danger',
  }[primaryIcon] || ''

  return (
    <>
      {/* v0.2: Atmospheric Background (Council Phase B1) */}
      <AtmosphericBackground icon={primaryIcon} ephemeris={ephemeris} />

      {/* v0.2: Rain Particles (Council Phase B2) */}
      {isRaining && <RainLayer intensity={decision?.animation_intensity || 'moderate'} />}

      <div className={`app-container ${glowColorClass}`}>
        {/* Location indicator */}
        <div className="location-bar">
          <button
            className="location-name"
            onClick={() => setShowLocations(true)}
            aria-label={`Location: ${selectedLocation?.name || 'Paris'}`}
          >
            {FLAGS[selectedLocation?.country] || '📍'} {selectedLocation?.name || 'Paris'}
          </button>
        </div>

        {/* Streak badge */}
        {streak && streak.current_streak > 0 && (
          <div className="streak-badge animate-fadeIn" aria-label={`Streak: ${streak.current_streak} days`}>
            🔥 {streak.current_streak}
          </div>
        )}

        {/* Main icon area with entrance animation (Council Phase B3) */}
        <div className="main-icon-area">
          {decision && (
            <div className={entered ? 'animate-entrance' : ''} style={{ opacity: entered ? 1 : 0 }}>
              <WeatherIcon
                icon={primaryIcon}
                intensity={decision.animation_intensity}
                glow={decision.confidence_glow}
                primary={true}
                onLongPress={() => setShowExplain(true)}
                onClick={refresh}
                ariaLabel={`Weather: ${primaryIcon}. Confidence: ${Math.round(decision.confidence_glow * 100)}%`}
              />
            </div>
          )}
          {decision?.secondary_icon && (
            <WeatherIcon
              icon={decision.secondary_icon}
              intensity="calm"
              glow={0}
              primary={false}
              ariaLabel={`Also: ${decision.secondary_icon}`}
            />
          )}
        </div>

        {/* Feedback buttons with celebration (Council Phase C4) */}
        {decision?.decision_id && (
          <div className="feedback-area animate-slideUp">
            <button
              className={`feedback-btn correct ${celebrating ? 'celebrating animate-celebrate' : ''}`}
              onClick={() => handleFeedback('correct')}
              aria-label="Decision was correct"
            >
              👍
              <span className="burst" />
            </button>
            <button
              className="feedback-btn wrong"
              onClick={() => handleFeedback('wrong')}
              aria-label="Decision was wrong"
            >
              👎
            </button>
          </div>
        )}

        {/* Toast */}
        {toast && <div className="toast">{toast}</div>}

        {/* v0.2: History Strip (Council Phase C2) */}
        <HistoryStrip decisions={recentDecisions} />

        {/* v0.2: Demo Badge (Council Phase A7) */}
        {isDemoData && <div className="demo-badge">Demo</div>}

        {/* Bottom navigation */}
        <div className="bottom-bar">
          <button className="bottom-btn active" onClick={refresh} aria-label="Refresh weather">
            🌦️
          </button>
          <button className="bottom-btn" onClick={() => setShowLocations(true)} aria-label="Choose location">
            📍
          </button>
          <button className="bottom-btn" onClick={() => setShowExplain(true)} aria-label="Explain decision">
            💡
          </button>
        </div>

        {/* Overlays */}
        {showExplain && (
          <ExplainOverlay
            decision={decision}
            weather={weather}
            ephemeris={ephemeris}
            onClose={() => setShowExplain(false)}
          />
        )}

        {showLocations && (
          <LocationSelector
            locations={locations}
            selected={selectedLocation}
            onSelect={(loc) => {
              setSelectedLocation(loc)
              // v0.3: Save new selection to localStorage
              localStorage.setItem('uos_location', JSON.stringify({
                name: loc.name, country: loc.country,
                lat: loc.latitude, lon: loc.longitude,
                savedAt: new Date().toISOString(),
              }))
            }}
            onClose={() => setShowLocations(false)}
            onReset={() => {
              // v0.3: Reset setup — clear localStorage and show setup
              localStorage.removeItem('uos_location')
              setNeedsSetup(true)
            }}
          />
        )}
      </div>
    </>
  )
}
