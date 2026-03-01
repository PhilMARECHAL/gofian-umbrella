/**
 * GOFIAN UoS — Country Flag Utility
 * Converts ISO 3166-1 alpha-2 country codes to flag emojis.
 * Uses Unicode Regional Indicator Symbols.
 */

export function countryToFlag(countryCode) {
  if (!countryCode || typeof countryCode !== 'string' || countryCode.length !== 2) return ''
  return countryCode
    .toUpperCase()
    .replace(/./g, c => String.fromCodePoint(c.charCodeAt(0) + 127397))
}

/**
 * Get country display name from code (basic mapping for common countries)
 */
const COUNTRY_NAMES = {
  FR: 'France', GB: 'United Kingdom', US: 'United States', DE: 'Germany',
  ES: 'Spain', IT: 'Italy', JP: 'Japan', CN: 'China', AU: 'Australia',
  CA: 'Canada', BR: 'Brazil', IN: 'India', RU: 'Russia', MX: 'Mexico',
  KR: 'South Korea', NL: 'Netherlands', BE: 'Belgium', CH: 'Switzerland',
  PT: 'Portugal', SE: 'Sweden', NO: 'Norway', DK: 'Denmark', FI: 'Finland',
  PL: 'Poland', AT: 'Austria', GR: 'Greece', TR: 'Turkey', EG: 'Egypt',
  ZA: 'South Africa', AR: 'Argentina', CO: 'Colombia', CL: 'Chile',
  TH: 'Thailand', ID: 'Indonesia', MY: 'Malaysia', SG: 'Singapore',
  NZ: 'New Zealand', IE: 'Ireland', IL: 'Israel', AE: 'UAE',
  SA: 'Saudi Arabia', MA: 'Morocco', CY: 'Cyprus', CZ: 'Czechia',
  RO: 'Romania', HU: 'Hungary', HR: 'Croatia', IS: 'Iceland',
  LU: 'Luxembourg', UA: 'Ukraine', PH: 'Philippines', VN: 'Vietnam',
}

export function countryName(code) {
  if (!code) return ''
  return COUNTRY_NAMES[code.toUpperCase()] || code.toUpperCase()
}
