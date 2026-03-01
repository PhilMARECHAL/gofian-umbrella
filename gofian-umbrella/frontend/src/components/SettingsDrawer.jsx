/**
 * GOFIAN UoS v0.4.0 — SettingsDrawer Component
 * Compact bottom sheet for changing location settings.
 * Replaces the old LocationSelector overlay.
 */
import { useState, useEffect, useCallback } from 'react'
import CitySearch from './CitySearch'
import { countryToFlag } from '../utils/countryFlag'

export default function SettingsDrawer({ isOpen, onClose, onLocationChange, currentLocation, savedLocations }) {
  const [gpsLoading, setGpsLoading] = useState(false)

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return
    const handleKey = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [isOpen, onClose])

  // GPS re-detect
  const handleGPS = useCallback(async () => {
    if (!navigator.geolocation) return
    setGpsLoading(true)

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude: lat, longitude: lon } = pos.coords
        // Reverse geocode to get city name
        try {
          const res = await fetch(`/api/v1/geocode/reverse?lat=${lat}&lon=${lon}`)
          const data = await res.json()
          const geo = data.data || {}
          onLocationChange({
            name: geo.city || 'My Location',
            country: geo.country || '',
            latitude: lat,
            longitude: lon,
            lat, lon,
            street: geo.street || '',
            neighborhood: geo.neighborhood || '',
            isGPS: true,
          })
        } catch {
          onLocationChange({
            name: 'My Location',
            country: '',
            latitude: lat, longitude: lon,
            lat, lon,
            isGPS: true,
          })
        }
        setGpsLoading(false)
      },
      () => {
        setGpsLoading(false)
      },
      { enableHighAccuracy: true, timeout: 10000 }
    )
  }, [onLocationChange])

  // Handle city selection from CitySearch
  const handleCitySelect = useCallback((city) => {
    onLocationChange({
      name: city.name,
      country: city.country,
      latitude: city.lat,
      longitude: city.lon,
      lat: city.lat,
      lon: city.lon,
      state: city.state || '',
    })
  }, [onLocationChange])

  // Handle saved location selection
  const handleSavedSelect = useCallback((loc) => {
    onLocationChange({
      name: loc.name || loc.city,
      country: loc.country || '',
      latitude: loc.latitude,
      longitude: loc.longitude,
      lat: loc.latitude,
      lon: loc.longitude,
    })
  }, [onLocationChange])

  if (!isOpen) return null

  return (
    <>
      <div className="settings-drawer-backdrop" onClick={onClose} />
      <div className="settings-drawer" role="dialog" aria-label="Location settings">
        <div className="settings-drawer__handle" />

        <h3 className="settings-drawer__title">📍 Change Location</h3>

        {/* GPS button */}
        <button
          className="settings-drawer__gps-btn"
          onClick={handleGPS}
          disabled={gpsLoading}
        >
          {gpsLoading ? '📡 Detecting...' : '📍 Use my location'}
        </button>

        {/* City search */}
        <div className="settings-drawer__search">
          <CitySearch onSelect={handleCitySelect} placeholder="Search a city..." autoFocus={true} />
        </div>

        {/* Saved locations */}
        {savedLocations && savedLocations.length > 0 && (
          <div className="settings-drawer__saved">
            <div className="settings-drawer__saved-title">Saved locations</div>
            {savedLocations.map((loc) => (
              <button
                key={loc.id || loc.name}
                className={`settings-drawer__saved-item ${
                  currentLocation?.name === loc.name ? 'settings-drawer__saved-item--active' : ''
                }`}
                onClick={() => handleSavedSelect(loc)}
              >
                <span>{countryToFlag(loc.country)} {loc.name || loc.city}</span>
                {loc.is_home && <span className="settings-drawer__home">🏠</span>}
              </button>
            ))}
          </div>
        )}
      </div>
    </>
  )
}
