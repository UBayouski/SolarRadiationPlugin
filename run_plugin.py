#!/usr/bin/python

from __future__ import print_function

from solar_radiation import SolarRadiation

if __name__ == '__main__':
    # Start new instance of Solar Radiation class
    solar_radiation = SolarRadiation()
    # Parse config
    print('Parsed config: ', solar_radiation.parse_config())

    print('Sunrise: {0}\r\nSunset: {1}'.format(solar_radiation.get_sunrise_sunset()))
    print('Day Time: ', solar_radiation.is_day)
    print('Day of Year: ', solar_radiation.day_of_year)
    print('Solar Radiation, W/m2: ', solar_radiation.calcluate_solar_radiation())
