// Open-Meteo: free, no API key.
const CODES = [
  [[0], 'Clear'],
  [[1, 2], 'Partly cloudy'],
  [[3], 'Overcast'],
  [[45, 48], 'Fog'],
  [[51, 53, 55, 56, 57], 'Drizzle'],
  [[61, 63, 65, 66, 67, 80, 81, 82], 'Rain'],
  [[71, 73, 75, 77, 85, 86], 'Snow'],
  [[95, 96, 99], 'Thunderstorm'],
];

export const describeWeather = (code) => CODES.find(([codes]) => codes.includes(code))?.[1] ?? 'Unknown';

export async function getWeather({ latitude, longitude, fetchImpl = fetch }) {
  const url = new URL('https://api.open-meteo.com/v1/forecast');
  url.search = new URLSearchParams({
    latitude,
    longitude,
    current: 'temperature_2m,weather_code,wind_speed_10m',
    daily: 'temperature_2m_max,temperature_2m_min,precipitation_probability_max',
    forecast_days: '1',
    timezone: 'auto',
  });
  const res = await fetchImpl(url, { signal: AbortSignal.timeout(8000) });
  if (!res.ok) throw new Error(`Weather HTTP ${res.status}`);
  const data = await res.json();
  return {
    temperature: Math.round(data.current.temperature_2m),
    wind: Math.round(data.current.wind_speed_10m),
    condition: describeWeather(data.current.weather_code),
    high: Math.round(data.daily.temperature_2m_max[0]),
    low: Math.round(data.daily.temperature_2m_min[0]),
    rainChance: data.daily.precipitation_probability_max[0],
    units: data.current_units?.temperature_2m ?? '°C',
  };
}
