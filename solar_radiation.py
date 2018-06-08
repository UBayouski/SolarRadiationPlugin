import datetime, dateutil.parser, json, math, os, pytz, urllib, yaml

class SolarRadiation(object):

    def __init__(self):
        self.config = None
        self.sunrise = None
        self.sunset = None

        self._timezone = None
        self._today = None

    @property
    def is_date_today(self):
        return self.today == self.current_date.date()

    @property
    def timezone(self):
        if not self._timezone:
            self._timezone = pytz.timezone(self.config['TIME_ZONE'] or pytz.utc)
        
        return self._timezone

    @property
    def today(self):
        if not self._today:
            self._today = self.current_date.date()
        
        return self._today

    @property
    def current_date(self):
        return datetime.datetime.now(tz=self.timezone)

    @property
    def current_hour(self):
        current_time =  self.current_date.astimezone(self.timezone).time()
        return current_time.hour + current_time.minute / 60.0

    @property
    def is_day(self):
        return self.sunrise <= self.current_date <= self.sunset

    @property
    def day_of_year(self):
        return self.current_date.timetuple().tm_yday

    @property
    def sunrise_sunset_url(self):
        return 'https://api.sunrise-sunset.org/json?lat={0}&lng={1}&date=today&formatted=0'.format(self.latitude, self.config['LONGITUDE'])

    @property
    def latitude(self):
        return self.config['LATITUDE'] if self.config else None

    @staticmethod
    def declination_angle(day):
        return 23.45 * math.sin(math.radians(360.0 / 365 * (day - 81)))

    @staticmethod
    def air_mass(hour, day, latitude):
        """http://www.pveducation.org/pvcdrom/properties-of-sunlight/air-mass"""
        declination_angle = math.radians(SolarRadiation.declination_angle(day));
        hour_angle = math.radians(SolarRadiation.hour_angle(hour));
        elevation_angle = SolarRadiation.elevation_angle(hour_angle, declination_angle, latitude)
        declanation = math.radians(90) - elevation_angle;
        return 1 / (1E-4 + math.cos(declanation))

    @staticmethod
    def hour_angle(hour):
        """https://www.pveducation.org/pvcdrom/2-properties-sunlight/solar-time"""
        return 15 * (hour - 12);

    @staticmethod
    def elevation_angle(hour_angle, declanation_angle, latitude):
        """The elevation angle (used interchangeably with altitude angle) is the angular height of the sun in the sky measured from the horizontal.

        http://www.pveducation.org/pvcdrom/properties-of-sunlight/elevation-angle
        Args:
            hour_angle (int): hour angle in radians
        Returns:
            int: elevation angle in radians
        """
        return math.asin(math.sin(declanation_angle) * math.sin(latitude) + math.cos(declanation_angle) * math.cos(latitude) * math.cos(hour_angle))

    def get_sunrise_sunset(self):
        if (self.config and (not self.sunrise or not self.sunset or not self.is_date_today)):
            self._today = self.current_date.date()
            response = urllib.urlopen(self.sunrise_sunset_url)
            data = json.loads(response.read())
            result = data['results']
            sunrise = result['sunrise']
            sunset = result['sunset']
            self.sunrise = dateutil.parser.parse(sunrise).astimezone(self.timezone)
            self.sunset = dateutil.parser.parse(sunset).astimezone(self.timezone)
        
        return (self.sunrise, self.sunset)

    def calcluate_solar_radiation(self):
        """http://www.pveducation.org/pvcdrom/properties-of-sunlight/calculation-of-solar-insolation"""
        if (self.config):
            self.get_sunrise_sunset()

            if self.is_day:
                air_mass = SolarRadiation.air_mass(self.current_hour, self.day_of_year, self.latitude)
                result = math.pow(0.7, air_mass)
                result = 1353 * math.pow(result, 0.678)

                # We ignore case more than 1100 W/m2, because the peak solar radiation is 1 kW/m2
                # http://www.pveducation.org/pvcdrom/average-solar-radiation
                return 0 if result > 1100 else result

        return None

    def parse_config(self):
        """Parses config file if any"""
        file_name = '{}/solar_radiaton.yaml'.format(os.path.dirname(os.path.abspath(__file__)))

        if os.path.isfile(file_name):
            self.config = yaml.safe_load(open(file_name))

        return self.config