/**
 * GOFIAN UoS v0.4.0 — LocationHeader Component
 * Prominent location display with flag, city, street/neighborhood, and settings gear.
 */
import { countryToFlag, countryName } from '../utils/countryFlag'

export default function LocationHeader({ city, country, street, neighborhood, onSettingsClick }) {
  const flag = countryToFlag(country)
  const displayCountry = countryName(country)

  // Build street line
  let streetLine = ''
  if (street && neighborhood) {
    streetLine = `${street}, ${neighborhood}`
  } else if (street) {
    streetLine = street
  } else if (neighborhood) {
    streetLine = neighborhood
  }

  return (
    <div className="location-header" role="banner" aria-label={`Location: ${city}, ${displayCountry}`}>
      <div className="location-header__info">
        <div className="location-header__city">
          {flag && <span className="location-header__flag" aria-hidden="true">{flag}</span>}
          <span>{city || 'Unknown'}{displayCountry ? `, ${displayCountry}` : ''}</span>
        </div>
        {streetLine && (
          <div className="location-header__street" aria-label={`Near ${streetLine}`}>
            {streetLine}
          </div>
        )}
      </div>
      <button
        className="location-header__settings-btn"
        onClick={onSettingsClick}
        aria-label="Change location settings"
        title="Settings"
      >
        ⚙️
      </button>
    </div>
  )
}
