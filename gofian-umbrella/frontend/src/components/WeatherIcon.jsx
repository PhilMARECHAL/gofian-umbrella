import React from 'react'

/**
 * Icon mapping: decision engine icon names → emoji + CSS accent color
 */
const ICON_MAP = {
  sunglasses: { emoji: '☀️', color: 'var(--accent-sun)' },
  umbrella:   { emoji: '🌧️', color: 'var(--accent-rain)' },
  wind:       { emoji: '🌬️', color: 'var(--accent-wind)' },
  cold:       { emoji: '❄️', color: 'var(--accent-cold)' },
  heat:       { emoji: '🔥', color: 'var(--accent-heat)' },
  sunrise:    { emoji: '🌅', color: 'var(--accent-sun)' },
  sunset:     { emoji: '🌇', color: 'var(--accent-sun)' },
  danger:     { emoji: '⚠️', color: 'var(--accent-danger)' },
  clear:      { emoji: '✨', color: 'var(--text-secondary)' },
}

/**
 * v0.2: Icon-specific animation classes (Council Phase A1, A2)
 * Umbrella gets rain-drip, wind gets wind-sway, others get pulse
 */
const ICON_ANIMATIONS = {
  umbrella: { calm: 'animate-rain-drip', moderate: 'animate-moderate', intense: 'animate-intense', urgent: 'animate-urgent' },
  wind:     { calm: 'animate-wind-sway', moderate: 'animate-wind-sway', intense: 'animate-intense', urgent: 'animate-urgent' },
}

/**
 * WeatherIcon — Primary or secondary animated icon
 * v0.2: Icon-specific animations, color-coded glow, aria-labels
 */
export default function WeatherIcon({
  icon = 'sunglasses',
  intensity = 'calm',
  glow = 0.5,
  primary = true,
  onLongPress,
  onClick,
  ariaLabel,
}) {
  const iconData = ICON_MAP[icon] || ICON_MAP.clear
  // v0.2: Use icon-specific animation if available (Council A1, A2)
  const iconAnims = ICON_ANIMATIONS[icon]
  const animClass = iconAnims ? (iconAnims[intensity] || `animate-${intensity}`) : `animate-${intensity}`

  // Glow level
  let glowClass = 'glow-low'
  if (glow > 0.8) glowClass = 'glow-max'
  else if (glow > 0.6) glowClass = 'glow-high'
  else if (glow > 0.4) glowClass = 'glow-medium'

  // Long-press handling
  const timerRef = React.useRef(null)

  const handleTouchStart = () => {
    timerRef.current = setTimeout(() => {
      if (onLongPress) onLongPress()
    }, 500)
  }

  const handleTouchEnd = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }

  const handleMouseDown = () => {
    timerRef.current = setTimeout(() => {
      if (onLongPress) onLongPress()
    }, 500)
  }

  const handleMouseUp = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }

  if (primary) {
    return (
      <div
        className={`glow-container ${glowClass} animate-fadeIn`}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 'clamp(180px, 45vw, 280px)',
          height: 'clamp(180px, 45vw, 280px)',
        }}
      >
        <span
          className={`primary-icon ${animClass}`}
          onClick={onClick}
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          role="img"
          aria-label={ariaLabel || `Weather: ${icon}`}
        >
          {iconData.emoji}
        </span>
      </div>
    )
  }

  return (
    <span
      className={`secondary-icon animate-float animate-fadeIn`}
      role="img"
      aria-label={ariaLabel || `Also: ${icon}`}
    >
      {iconData.emoji}
    </span>
  )
}
