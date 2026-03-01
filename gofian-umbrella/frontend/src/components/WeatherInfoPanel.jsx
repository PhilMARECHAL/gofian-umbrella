/**
 * GOFIAN UoS v0.4.3 — Ghost Grid with Emoji Labels
 * Council of Ten: "Emoji IS the label. Zero text. Universal."
 *
 * Each stat = one emoji + one bold number. Nothing else.
 * The emoji breathes gently. Touch = scale + glow.
 * No sublabels, no descriptions, no demo text.
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

function uvColorClass(uv) {
  if (uv == null) return ''
  if (uv < 3) return 'ghost--low'
  if (uv < 6) return 'ghost--medium'
  return 'ghost--high'
}

function GhostStat({ emoji, value, colorClass, delay, ariaLabel }) {
  return (
    <div
      className="ghost-stat"
      style={{ '--cascade-delay': `${delay}s` }}
      aria-label={ariaLabel}
    >
      <span className="ghost-stat__emoji">{emoji}</span>
      <span className={`ghost-stat__value ${colorClass || ''}`}>{value}</span>
    </div>
  )
}

export default function WeatherInfoPanel({ weather, ephemeris }) {
  if (!weather) return null

  const temp = weather.temperature_c
  const feelsLike = weather.feels_like_c
  const rainProb = weather.rain_probability
  const uv = weather.uv_index
  const wind = weather.wind_speed_kmh
  const sunrise = ephemeris?.sunrise
  const sunset = ephemeris?.sunset

  // Temperature display: "7°" or "7°/4°" if feels different
  const tempStr = temp != null
    ? (feelsLike != null && Math.abs(temp - feelsLike) >= 2
        ? `${Math.round(temp)}°/${Math.round(feelsLike)}°`
        : `${Math.round(temp)}°`)
    : '--'

  return (
    <div className="ghost-grid" role="region" aria-label="Weather details">
      <div className="ghost-grid__stats">
        <GhostStat
          emoji="🌡️"
          value={tempStr}
          colorClass={tempColorClass(temp)}
          delay={0.1}
          ariaLabel={`Temperature ${temp != null ? Math.round(temp) + '°C' : 'unavailable'}`}
        />
        <GhostStat
          emoji="🌧️"
          value={rainProb != null ? `${Math.round(rainProb * 100)}%` : '--'}
          colorClass={rainColorClass(rainProb)}
          delay={0.2}
          ariaLabel={`Rain ${rainProb != null ? Math.round(rainProb * 100) + '%' : 'unavailable'}`}
        />
        <GhostStat
          emoji="☀️"
          value={uv != null ? uv.toFixed(1) : '--'}
          colorClass={uvColorClass(uv)}
          delay={0.3}
          ariaLabel={`UV index ${uv != null ? uv.toFixed(1) : 'unavailable'}`}
        />
        <GhostStat
          emoji="💨"
          value={wind != null ? `${Math.round(wind)}` : '--'}
          delay={0.4}
          ariaLabel={`Wind ${wind != null ? Math.round(wind) + ' km/h' : 'unavailable'}`}
        />
        <GhostStat
          emoji="🌅"
          value={sunrise || '--'}
          delay={0.5}
          ariaLabel={`Sunrise ${sunrise || 'unavailable'}`}
        />
        <GhostStat
          emoji="🌇"
          value={sunset || '--'}
          delay={0.6}
          ariaLabel={`Sunset ${sunset || 'unavailable'}`}
        />
      </div>
    </div>
  )
}
