import type { WeatherParams } from '../services/api';

export const DEFAULT_WEATHER: WeatherParams = {
  ambient_temp: 25,
  wind_speed: 2.0,
  wind_angle: 90,
  sun_time: 12,
  date: '12 Jun',
  elevation: 1000,
  latitude: 27,
  emissivity: 0.8,
  absorptivity: 0.8,
  direction: 'EastWest',
  atmosphere: 'Clear'
};
