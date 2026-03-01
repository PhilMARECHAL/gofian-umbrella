/**
 * GOFIAN UoS v0.4.0 — WeatherInfoPanel Component
 * Glassmorphic panel showing 6 weather data points.
 * Council of Ten: Weather Expert approved layout.
 */

function tempColorClass(t) {
  if (t == null) return ''
  if (t <= 0) return 'stat--freezing'
  if (t <= 5) return 'stat--cold'
  if (t <= 25) return ''
  if (t <= 32) return 'stat--warm'
  return 'stat--hot'
}

function rainColorClass(p) {
  if (p == null) return ''
  if (p < 0.30) return 'stat--rain-low'
  if (p < 0.60) return 'stat--rain-medium'
  return 'stat--rain-high'
}

function uvLabel(uv) {
  if (uv == null) return ''
  if (uv < 3) return 'Low'
  if (uv < 6) return 'Moderate'
  if (uv < 8) return 'High'
  if (uv < 11) return 'Very High'
  return 'Extreme'
}

function uvColorClass(uv) {
  if (uv == null) return ''
  if (uv < 3) return 'stat--rain-low'
  if (uv < 6) return 'stat--warm'
  if (uv < 8) return 'stat--hot'
  return 'stat--freezing'
}

function WeatherStat({ icon, value, sublabel, colorClass, ariaLabel }) {
  return (
    <div className="weather-stat" aria-label={ariaLabel}>
      <span className="weather-stat__icon" aria-hidden="true">{icon}</span>
      <span className={`weather-stat__value ${colorClass || ''}`}>{value}</span>
      {sublabel && <span className="weather-stat__sub">{sublabel}</span>}
    </div>
  )
}

// Map weather condition to emoji
function weatherEmoji(condition, icon) {
  if (!condition) return '🌤️'
  const c = condition.toLowerCase()
  if (c.includes('thunder')) return '⛈️'
  if (c.includes('drizzle')) return '🌦️'
  if (c.includes('rain')) return '🌧️'
  if (c.includes('snow')) return '🌨️'
  if (c.includes('mist') || c.includes('fog') || c.includes('haze')) return '🌫️'
  if (c.includes('cloud')) {
    if (icon && icon.includes('n')) return '☁️'
    return '⛅'
  }
  if (icon && icon.includes('n')) return '🌙'
  return '☀️'
}

export default function WeatherInfoPanel({ weather, ephemeris, decision, onMoreDetails }) {
  if (!weather) return null

  const temp = weather.temperature_c
  const feelsLike = weather.feels_like_c
  const rainProb = weather.rain_probability
  const uv = weather.uv_index
  const wind = weather.wind_speed_kmh
  const gust = weather.wind_gust_kmh
  const sunrise = ephemeris?.sunrise
  const sunset = ephemeris?.sunset
  const condition = weather.weather_description
  const weatherIcon = weather.weather_icon

  return (
    <div className="weather-info-panel animate-slideUp">
      {/* Sky description */}
      <div className="weather-info-panel__description">
        {weatherEmoji(weather.weather_condition, weatherIcon)}{' '}
        {condition || 'No data'}
      </div>

      {/* 2x3 grid of stats */}
      <div className="weather-info-grid">
        <WeatherStat
          icon="🌡️"
          value={temp != null ? `${Math.round(temp)}°C` : '--'}
          sublabel={feelsLike != null ? `Feels ${Math.round(feelsLike)}°` : null}
          colorClass={tempColorClass(temp)}
          ariaLabel={`Temperature: ${temp != null ? Math.round(temp) + ' degrees' : 'unavailable'}`}
        />
        <WeatherStat
          icon="🌧️"
          value={rainProb != null ? `${Math.round(rainProb * 100)}%` : '--'}
          sublabel="Rain"
          colorClass={rainColorClass(rainProb)}
          ariaLabel={`Rain probability: ${rainProb != null ? Math.round(rainProb * 100) + ' percent' : 'unavailable'}`}
        />
        <WeatherStat
          icon="☀️"
          value={uv != null ? uv.toFixed(1) : '--'}
          sublabel={uv != null ? uvLabel(uv) : 'UV'}
          colorClass={uvColorClass(uv)}
          ariaLabel={`UV index: ${uv != null ? uv.toFixed(1) + ', ' + uvLabel(uv) : 'unavailable'}`}
        />
        <WeatherStat
          icon="💨"
          value={wind != null ? `${Math.round(wind)}` : '--'}
          sublabel={gust ? `Gusts ${Math.round(gust)} km/h` : 'km/h'}
          ariaLabel={`Wind speed: ${wind != null ? Math.round(wind) + ' km/h' : 'unavailable'}`}
        />
        <WeatherStat
          icon="🌅"
          value={sunrise || '--'}
          sublabel="Sunrise"
          ariaLabel={`Sunrise at ${sunrise || 'unavailable'}`}
        />
        <WeatherStat
          icon="🌇"
          value={sunset || '--'}
          sublabel="Sunset"
          ariaLabel={`Sunset at ${sunset || 'unavailable'}`}
        />
      </div>

      {/* Source + more details */}
      <div className="weather-info-panel__footer">
        <span className="weather-info-panel__source">
          {weather.source === 'demo' ? '⚠️ Demo data' : `📡 ${weather.source || 'API'}`}
        </span>
        {onMoreDetails && (
          <button className="weather-info-panel__more" onClick={onMoreDetails}>
            More details
          </button>
        )}
      </div>
    </div>
  )
}
