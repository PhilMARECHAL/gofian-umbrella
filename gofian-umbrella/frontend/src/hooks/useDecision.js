import { useState, useEffect, useCallback } from 'react'

const API = '/api/v1'

export function useDecision(lat, lon) {
  const [decision, setDecision] = useState(null)
  const [weather, setWeather] = useState(null)
  const [ephemeris, setEphemeris] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchDecision = useCallback(async () => {
    if (lat == null || lon == null) return
    setLoading(true)
    setError(null)
    try {
      const [decRes, weatherRes, ephemRes] = await Promise.all([
        fetch(`${API}/decide?lat=${lat}&lon=${lon}`),
        fetch(`${API}/weather?lat=${lat}&lon=${lon}`),
        fetch(`${API}/ephemeris?lat=${lat}&lon=${lon}`),
      ])
      const [decData, weatherData, ephemData] = await Promise.all([
        decRes.json(),
        weatherRes.json(),
        ephemRes.json(),
      ])
      setDecision(decData.data)
      setWeather(weatherData.data)
      setEphemeris(ephemData.data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [lat, lon])

  useEffect(() => {
    fetchDecision()
  }, [fetchDecision])

  return { decision, weather, ephemeris, loading, error, refresh: fetchDecision }
}

export function useStreak() {
  const [streak, setStreak] = useState(null)

  const fetchStreak = useCallback(async () => {
    try {
      const res = await fetch(`${API}/streak`)
      const data = await res.json()
      setStreak(data.data)
    } catch (err) {
      console.warn('Failed to fetch streak:', err)
    }
  }, [])

  const checkIn = useCallback(async () => {
    try {
      const res = await fetch(`${API}/streak/check-in`, { method: 'POST' })
      const data = await res.json()
      setStreak(data.data)
      return data
    } catch (err) {
      console.warn('Failed to check in:', err)
      return null
    }
  }, [])

  useEffect(() => {
    fetchStreak()
  }, [fetchStreak])

  return { streak, checkIn, refresh: fetchStreak }
}

export function useLocations() {
  const [locations, setLocations] = useState([])

  const fetchLocations = useCallback(async () => {
    try {
      const res = await fetch(`${API}/locations`)
      const data = await res.json()
      setLocations(data.data || [])
    } catch (err) {
      console.warn('Failed to fetch locations:', err)
    }
  }, [])

  useEffect(() => {
    fetchLocations()
  }, [fetchLocations])

  return { locations, refresh: fetchLocations }
}

export function useReverseGeocode(lat, lon) {
  const [geoData, setGeoData] = useState(null)
  const [geoLoading, setGeoLoading] = useState(false)

  useEffect(() => {
    if (lat == null || lon == null) return
    setGeoLoading(true)
    fetch(`${API}/geocode/reverse?lat=${lat}&lon=${lon}`)
      .then(r => r.json())
      .then(d => setGeoData(d.data))
      .catch(() => setGeoData(null))
      .finally(() => setGeoLoading(false))
  }, [lat, lon])

  return { geoData, geoLoading }
}

export async function submitFeedback(decisionId, feedback) {
  try {
    const res = await fetch(`${API}/decisions/${decisionId}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feedback }),
    })
    return await res.json()
  } catch (err) {
    console.warn('Failed to submit feedback:', err)
    return null
  }
}
