import React, { useState, useCallback } from 'react'

const FLAGS = {
  FR: '🇫🇷', CY: '🇨🇾', US: '🇺🇸', JP: '🇯🇵', AU: '🇦🇺',
  GB: '🇬🇧', DE: '🇩🇪', ES: '🇪🇸', IT: '🇮🇹', BR: '🇧🇷',
  NL: '🇳🇱', AE: '🇦🇪', SG: '🇸🇬', CH: '🇨🇭', BE: '🇧🇪',
}

export default function LocationSelector({ locations, selected, onSelect, onClose, onReset }) {
  const [gpsLoading, setGpsLoading] = useState(false)

  const handleGPS = useCallback(() => {
    if (!navigator.geolocation) return
    setGpsLoading(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGpsLoading(false)
        onSelect({
          name: 'My Location',
          country: '',
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
        })
        onClose()
      },
      () => setGpsLoading(false),
      { enableHighAccuracy: true, timeout: 8000 }
    )
  }, [onSelect, onClose])

  return (
    <div className="location-selector" onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{ width: '100%', maxWidth: '340px' }}>
        <p className="location-title">📍</p>

        {/* GPS button */}
        <button
          className="location-gps-btn"
          onClick={handleGPS}
          disabled={gpsLoading}
        >
          {gpsLoading ? '📡 Locating...' : '🎯 Use my location'}
        </button>

        <div className="location-list">
          {locations.map(loc => (
            <div
              key={loc.id}
              className={`location-item ${selected?.name === loc.name ? 'selected' : ''}`}
              onClick={() => { onSelect(loc); onClose(); }}
            >
              <span className="location-item-name">
                {loc.is_home ? '🏠 ' : ''}{loc.name}
              </span>
              <span className="location-item-flag">
                {FLAGS[loc.country] || '🌍'}
              </span>
            </div>
          ))}
        </div>

        {/* Reset / Change city button */}
        {onReset && (
          <button
            className="location-reset-btn"
            onClick={() => { onReset(); onClose(); }}
          >
            ✨ Change my city
          </button>
        )}
      </div>
    </div>
  )
}
