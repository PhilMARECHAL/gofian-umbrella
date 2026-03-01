/**
 * GOFIAN UoS v0.4.2 — Ghost Grid WeatherInfoPanel
 * Council of Ten: Interaction Choreographer + Accessibility Lead
 *
 * Zero-chrome 3×2 invisible grid. Values float below the icon.
 * Each stat cascades in on load. Touch = golden thread + scale.
 * No borders, no backgrounds — just data breathing with the icon.
 */

function tempColorClass(t) {
  if (t == null) return ''
  if (t <= 0) return 'ghost--freezing'
  if (t <= 5) return 'ghost--cold'
  if (t <= 25) return ''
  if (t <= 32) return 'ghost--warm'
  return 'ghost--hot'
}

function rainColorClass(p) {
  if (p == null) return ''
  if (p < 0.30) return 'ghost--low'
  if (p < 0.60) return 'ghost--medium'
  return 'ghost--high'
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
  if (uv < 3) return 'ghost--low'
  if (uv < 6) return 'ghost--medium'
  return 'ghost--high'
}

function GhostStat({ value, sublabel, colorClass, delay, ariaLabel }) {
  return (
    <div
      className="ghost-stat"
      style={{ '--cascade-delay': `${delay}s` }}
      aria-label={ariaLabel}
    >
      <span className={`ghost-stat__value ${colorClass || ''}`}>{value}</span>
      {sublabel && <span className="ghost-stat__sub">{sublabel}</span>}
    </div>
  )
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

  return (
    <div className="ghost-grid" role="region" aria-label="Weather details">
      {/* Sky description — faint centered text */}
      <div className="ghost-grid__sky" style={{ '--cascade-delay': '0s' }}>
        {weather.source === 'demo' ? '🌙 Demo Data — Configure API Key For Real Weather' : (weather.weather_description || '')}
      </div>

      {/* 3×2 invisible grid */}
      <div className="ghost-grid__stats">
        <GhostStat
          value={temp != null ? `${Math.round(temp)}°C` : '--'}
          sublabel={feelsLike != null ? `Feels ${Math.round(feelsLike)}°` : null}
          colorClass={tempColorClass(temp)}
          delay={0.1}
          ariaLabel={`Temperature: ${temp != null ? Math.round(temp) + '°C' : 'unavailable'}`}
        />
        <GhostStat
          value={rainProb != null ? `${Math.round(rainProb * 100)}%` : '--'}
          sublabel="Rain"
          colorClass={rainColorClass(rainProb)}
          delay={0.2}
          ariaLabel={`Rain: ${rainProb != null ? Math.round(rainProb * 100) + '%' : 'unavailable'}`}
        />
        <GhostStat
          value={uv != null ? uv.toFixed(1) : '--'}
          sublabel={uv != null ? uvLabel(uv) : 'UV'}
          colorClass={uvColorClass(uv)}
          delay={0.3}
          ariaLabel={`UV: ${uv != null ? uv.toFixed(1) : 'unavailable'}`}
        />
        <GhostStat
          value={wind != null ? `${Math.round(wind)}` : '--'}
          sublabel={gust ? `Gusts ${Math.round(gust)} km/h` : 'km/h'}
          delay={0.4}
          ariaLabel={`Wind: ${wind != null ? Math.round(wind) + ' km/h' : 'unavailable'}`}
        />
        <GhostStat
          value={sunrise || '--'}
          sublabel="Sunrise"
          delay={0.5}
          ariaLabel={`Sunrise: ${sunrise || 'unavailable'}`}
        />
        <GhostStat
          value={sunset || '--'}
          sublabel="Sunset"
          delay={0.6}
          ariaLabel={`Sunset: ${sunset || 'unavailable'}`}
        />
      </div>
    </div>
  )
}
