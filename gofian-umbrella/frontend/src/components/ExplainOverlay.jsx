import React from 'react'

/**
 * ExplainOverlay — Long-press reveal (Contrarian + Guardian approved)
 * Shows a one-line explanation without polluting the default icon-only experience.
 * v0.4: Weather data grid and ephemeris removed — now in WeatherInfoPanel.
 */
export default function ExplainOverlay({ decision, weather, ephemeris, onClose }) {
  if (!decision) return null

  const iconEmojis = {
    sunglasses: '☀️', umbrella: '🌧️', wind: '🌬️',
    cold: '❄️', heat: '🔥', danger: '⚠️',
    sunrise: '🌅', sunset: '🌇', clear: '✨',
  }

  return (
    <div className="explain-overlay" onClick={onClose}>
      <div className="explain-content" onClick={e => e.stopPropagation()}>
        <div className="explain-icon">
          {iconEmojis[decision.primary_icon] || '🌦️'}
        </div>

        <p className="explain-text">
          {decision.primary_reason}
        </p>

        {decision.secondary_icon && (
          <p className="explain-text" style={{ fontSize: '14px', opacity: 0.7 }}>
            {iconEmojis[decision.secondary_icon]} {decision.secondary_reason}
          </p>
        )}

        {/* v0.2: Data source disclosure (Council A7, Guardian requirement) */}
        {weather && (
          <div className="explain-source">
            {weather.source === 'demo'
              ? 'Based on demo estimates'
              : weather.source === 'openweathermap'
                ? 'Based on OpenWeatherMap data'
                : `Source: ${weather.source || 'unknown'}`}
          </div>
        )}

        {/* v0.2: Confidence indicator */}
        {decision.confidence_glow != null && (
          <div style={{
            marginTop: '8px',
            fontSize: '12px',
            color: 'var(--text-dim)',
            opacity: 0.6,
          }}>
            Confidence: {Math.round(decision.confidence_glow * 100)}%
          </div>
        )}

        <button className="explain-close" onClick={onClose} style={{ marginTop: '24px' }}>
          ✕
        </button>
      </div>
    </div>
  )
}
