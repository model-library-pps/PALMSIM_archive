#!/usr/bin/env python

""" Provides the interface to the weather data. """

import yaml
import pandas as pd

from .helpers import add_dumps
from .helpers import rad

from math import exp, sin, cos, sqrt, pi, acos, asin, log

PI = pi

SECONDS_PER_DAY = 24*60*60

@add_dumps
class Weather(object):
    """ Weather related logic.

    The instance of this class (singleton) loads the input weather data into memory and 
    calculates derived quantities.

    Time-series:
    - radiation_series
    - rainfall_series
    - humidity_series
    - temperature_series
    - windspeed_series

    Associated looked-up values:
    - radiation (MJ/m2/day)
    - rainfall (mm/day)
    - humidity (%)
    - temperature (degC)
    - wind speed (m/s)
    """

    parameters = yaml.load("""
    albedo:
        value: 0.14
        unit: '1'
        info: 'Albedo of a twelve year old oil palm'
        source: 'Meijide, A., Roll, A., Fan, Y., Herbst, M., Niu, F., Tiedemann,
                F., June, T., Rauf, A., Holscher, D., and Knohl, A. (2017). Controls
                of water and energy fluxes in oil palm plantations: environmental
                variables and oil palm age. Agricultural and Forest Meteorology,
                239:71-85.'

    crop_reference_albedo:
        value: 0.23
        unit: '1'
        info: 'Albedo of the reference crop'
        source: 'Allen, R., Pereira, L., Raes, D., and Smith, M. (1998c). 
                FAO Penman-Monteith Equation. In Allen, R., Pereira, L., 
                Raes, D., and Smith, M., editors, FAO Irrigation and Drainage
                Paper No. 56 - Crop Evapotranspiration (guidelines for computing
                crop water requirements), pages 15-27. Food and Agriculture 
                Organization of the United Nations.' 

    crop_reference_height:
        value: 0.12
        unit: 'm'
        info: 'Crop height of the reference crop'
        source: 'Allen, R., Pereira, L., Raes, D., and Smith, M. (1998c). 
                FAO Penman-Monteith Equation. In Allen, R., Pereira, L., 
                Raes, D., and Smith, M., editors, FAO Irrigation and Drainage
                Paper No. 56 - Crop Evapotranspiration (guidelines for computing
                crop water requirements), pages 15-27. Food and Agriculture 
                Organization of the United Nations.' 

    crop_reference_stomatal_resistance:
        value: 100
        unit: 's/m'
        info: 'Average minimum daytime value of stomatal resistance (s/m) for a
                single leaf.'
        source: 'Allen, R., Pereira, L., Raes, D., and Smith, M. (1998c). 
                FAO Penman-Monteith Equation. In Allen, R., Pereira, L., 
                Raes, D., and Smith, M., editors, FAO Irrigation and Drainage
                Paper No. 56 - Crop Evapotranspiration (guidelines for computing
                crop water requirements), pages 15-27. Food and Agriculture 
                Organization of the United Nations.' 

    crop_reference_surface_resistance:
        value: 70
        unit: 's/m'
        info: 'Surface resistance of the reference crop'
        source: 'Allen, R., Pereira, L., Raes, D., and Smith, M. (1998c). 
                FAO Penman-Monteith Equation. In Allen, R., Pereira, L., 
                Raes, D., and Smith, M., editors, FAO Irrigation and Drainage
                Paper No. 56 - Crop Evapotranspiration (guidelines for computing
                crop water requirements), pages 15-27. Food and Agriculture 
                Organization of the United Nations.'

    heat_capacity_dry_air:
        value: 1004
        unit: 'J/kg/degC'
        info: 'Assuming an air temperature of 20 degC.'
        source: 'Hilsenrath, J., Beckett, C., Benedict, W., Fano, L., Hoge, H.,
                Masi, J., Nuttal,R., Touloukian, Y., andWolley, H. (1955). 
                Tables of thermal properties of gases nbs circular 564. National\
                Bureau of Standards.'

    karman_constant:
        value: 0.41
        unit: '1'
        info: 'van Karman constant for turbulent diffusion'
        source: 'Allen, R., Pereira, L., Raes, D., and Smith, M. (1998c). 
                FAO Penman-Monteith Equation. In Allen, R., Pereira, L., 
                Raes, D., and Smith, M., editors, FAO Irrigation and Drainage
                Paper No. 56 - Crop Evapotranspiration (guidelines for computing
                crop water requirements), pages 15-27. Food and Agriculture 
                Organization of the United Nations.' 

    latent_heat_water:
        value: 2.454
        unit: 'MJ/kg'
        info: 'Assuming a constant air temperature of 20 deg. C'
        source: 'Allen, R., Pereira, L., Raes, D., and Smith, M. (1998c). 
                Meteorological data. In Allen, R., Pereira, L., Raes, D., 
                and Smith, M., editors, FAO Irrigation and Drainage Paper 
                No. 56 - Crop Evapotranspiration (guidelines for computing
                crop water requirements), pages 19-64. Food and Agriculture
                 Organization of the United Nations.'

    PAR_fraction:
        value: 0.5
        unit: '1'
        info: 'The fraction of photosynthetically active raidation in 
                irradiation.'
        source: 'Goudriaan, J. and Van Laar, H. (2004). The main seasonal
                growth pattern. In Goudriaan, J. and Van Laar, H., editors,
                Modelling potential crop growth processes: textbook with
                exercises, volume 2, chapter 2, pages 7-28. Springer Science
                & Business Media.'

    psychrometer_coefficient:
        value: 0.067
        unit: 'kPa/degC'
        info: 'psychrometer coefficient assuming a specific heat of air of 
                1.013E-3 MJ/kg/degC, a latent heat of vaporization of 
                2.45 MJ/kg, a molecular weight ratio of water vapour/dry air
                of 0.622 and an atmospheric pressure of 101.325 kPa.'
        source: 'Allen, R., Pereira, L., Raes, D., and Smith, M. (1998c). 
                Meteorological data. In Allen, R., Pereira, L., Raes, D., and
                Smith, M., editors, FAO Irrigation and Drainage Paper No. 
                56 - Crop Evapotranspiration (guidelines for computing crop
                water requirements), pages 19-64. Food and Agriculture 
                Organization of the United Nations.'

    ratio_molecular_weight:
        value: 0.622
        unit: '1'
        info: 'The ratio of molecular weight of water to the molecular weight of
                dry air. The molecular weight of water is 18.0152 g/mol and the 
                molecular weight of dry air is 28.963 g/mol.'
        source: 'Jones, F. E. (1977). The air density equation and the transfer of
                the mass unit. National Bureau of Standards.'

    reference_transmission_factor:
        value: 0.7
        unit: '1'
        info: 'reference transmission factor for clear skies'
        source: 'De Jong, J. B. R. M. (1980). Een karakterisering van de zonnestraling 
                in Nederland.'

    sigma:
        value: 5.670E-8
        unit: 'W/m2/K4'
        info: 'Stefan-Boltzmann constant.'
        source: 'The National Institue of Standards and Technology, 
                https://physics.nist.gov/, retreived 20-03-2019'

    solar_constant:
        value: 1367
        unit: 'J/m2/s'
        info: 'The incoming visible radiation,
                midday, above, the equator, at the edge of the atmosphere.
                Used to estimate the instantaneous radiation (J/m2/s)
                from the daily total radiation (MJ/m2/day).'
        source: 'Goudriaan, J. and Van Laar, H. (2004). Climatic factors. In
                Goudriaan, J. and Van Laar, H., editors, Modelling potential
                crop growth processes: textbook with exercises, volume 2,
                chapter 3, pages 29-48. Springer Science & Business Media.'

    specific_gas_constant:
        value: 0.287
        unit: 'kJ/kg/K'
        info: 'Stomatal resistance of a single leaf under well watered conditions'
        source: 'Allen, R., Pereira, L., Raes, D., and Smith, M. (1998c). 
                Meteorological data. In Allen, R., Pereira, L., Raes, D., and
                Smith, M., editors, FAO Irrigation and Drainage Paper No. 
                56 - Crop Evapotranspiration (guidelines for computing crop
                water requirements), pages 19-64. Food and Agriculture 
                Organization of the United Nations.' 

    swinbank_constant:
        value: 5.31E-13
        unit: 'J/m2/s'
        info: 'The swinbank constant'
        source: 'Swinbank, W. C. (1963). Long‐wave radiation from clear skies. 
                Quarterly Journal of the Royal Meteorological Society, 89(381), 
                339-348.'

    tilt_of_earth:
        value: 23.45
        unit: 'Deg'
        info: 'Is the angle between the earths rotational axis and its orbital
                axis, or, equivalently, the angle between its equatorial plane and
                its orbital plane.'
        source: 'Goudriaan, J. and Van Laar, H. (2004). Climatic factors. In
                Goudriaan, J. and Van Laar, H., editors, Modelling potential
                crop growth processes: textbook with exercises, volume 2,
                chapter 3, pages 29-48. Springer Science & Business Media.'
    """,
                           Loader=yaml.SafeLoader)

    units = {'aerodynamic_resistance'                 : 's/m',
             'bulk_surface_resistance'                : 's/m',
             'canopy_net_radiation_capture'           : 'MJ/m2/d',
             'canopy_net_radiation_capture_reference' : 'MJ/m2/d',
             'daylength'                              : 'hour',
             'weather_eccentricity_factor'            : '1',
             'eccentricity_factor'                    : '1',
             'ET_potential'                           : 'mm/d',
             'fraction_diffuse'                       : '1',
             'hour_of_dawn'                           : 'bool',
             'hour_of_dusk'                           : 'bool',
             'humidity'                               : '%',
             'humidity_series_mean'                   : '%',
             'PAR'                                    : 'MJ/m2/day',
             'radiation'                              : 'MJ/m2/day',
             'radiation_extraterrestrial_daily'       : 'MJ/m2/d',
             'radiation_longwave_sky_daily'           : 'MJ/m2/d',
             'radiation_series_mean'                  : 'MJ/m2/day',
             'rainfall'                               : 'mm/day',
             'rainfall_series_mean'                   : 'mm/day',
             'relative_humidity'                      : '1',
             'saturated_vapour_pressure'              : 'kPa',
             'saturated_vapour_pressure_slope'        : 'kPa/degC',
             'sine_solar_height_amplitude'            : '1',
             'sine_solar_height_mean'                 : '1',
             'temperature'                            : 'degC',
             'temperature_series_mean'                : 'degC',
             'transmission_factor'                    : '1',
             'vapour_pressure_deficit'                : 'kPa',
             'vapour_pressure_early_morning'          : 'kPa',
             'windspeed'                              : 'm/s',
             'windspeed_series_mean'                  : 'm/s'}

    _prefix = 'weather'

    def __init__(self,palm = None):

        self._palm = palm

        self.radiation_series = None
        self.rainfall_series  = None
        self.humidity_series = None
        self.temperature_series = None
        self.windspeed_series = None

        # Mean values - used
        # at times if no time-series data is available.
        self._radiation_series_mean = None
        self._rainfall_series_mean = None
        self._humidity_series_mean = None
        self._temperature_series_mean = None
        self._windspeed_series_mean = None

        # Mock-up values - only used in prototyping/testing
        self._radiation_series_mean_ = 20
        self._rainfall_series_mean_ = 150
        self._humidity_series_mean_ = 86
        self._temperature_series_mean_ = 28
        self._windspeed_series_mean_ = 2
        self._latitude_ = 0
        self._DOY_ = 1

        self.update()

    def set_sine_solar_height(self):
        self.sine_solar_height_mean = self.calc_sine_solar_height_mean()
        self.sine_solar_height_amplitude = self.calc_sine_solar_height_amplitude()

    def _set_DOY(self):

        self._DOY = self._get_DOY()

    def update(self):

        self._set_DOY()
        self.set_sine_solar_height()

    @property
    def _date_tuple(self):
        if self._palm:
            return self._palm.date_tuple
        else:
            return None

    #~~~~~~~~~~~~~~~~~~~

    @property
    def PAR(self):
        """ Photo-synthetically active radiation (MJ/m2/day). """
        c = self.parameters['PAR_fraction']['value']
        return c*self.radiation

    #~~~~~~~~~~~~~~~~~~~

    @property
    def radiation(self):
        """ Mean daily visible radiation (MJ/m2/day)."""
        t = self._date_tuple
        s = self.radiation_series
        if (t and s) and (t in s):
            return s[t]
        else:
            return self.radiation_series_mean

    @radiation.setter
    def radiation(self, value):

        if isinstance(value, (int, float)):
            self._radiation_series_mean_ = value
        else:
            raise ValueError

    @property
    def radiation_series(self):
        """ Mean daily visible radiation (MJ/m2/day) - time-series.

        A dict with a (year,day)-tuple keys and float values.
        """
        return self._radiation_series

    @radiation_series.setter
    def radiation_series(self,series):
        """ Sets the daily radiation time-series variable.

        Expects a date-time indexed time-series e.g.
        2007-01-01 00:00:00 - 12

        Furthermore, sets the all-time mean radiation -
        used by default in case of missing values.
        """

        if series is None:

            self._radiation_series = None
            self._radiation_series_mean = None

        elif isinstance(series, pd.Series):

            # to speed up fetching the data, we make a dictionary having the time as keys
            d = {(t.year,t.month,t.day): float(v) for t,v in series.iteritems()}

            self._radiation_series = d
            self._radiation_series_mean = float(series.mean())

        else:

            print(type(series))
            raise ValueError('Input a time-series.')

    @property
    def radiation_series_mean(self):
        """ The all-time mean of the mean-daily radiation (MJ/m2/day). """
        if self._radiation_series_mean:
            return self._radiation_series_mean
        else:
            return self._radiation_series_mean_

    # --------------------------------------

    @property
    def rainfall(self):
        """Daily rainfall (mm/d). """
        t = self._date_tuple
        s = self.rainfall_series

        if (t and s) and (t in s):
            res = s[t]
        else:
            res = self.rainfall_series_mean

        if res < 0: print('rainfall value out of range')
        assert res >= 0

        return res

    @rainfall.setter
    def rainfall(self, value):

        if isinstance(value, (int, float)):
            self._rainfall_series_mean_ = value
        else:
            raise ValueError

    @property
    def rainfall_series(self):
        """Monthly rainfall (mm/d) time-series.

        A dict with a (year,day)-tuple keys and float values.
        """
        return self._rainfall_series

    @rainfall_series.setter
    def rainfall_series(self,series):
        """ Sets the daily rainfall time-series variable.

        Expects a date-time indexed time-series e.g.
        2007-01-01 00:00:00 - 120

        Furthermore, sets the all-time mean rainfall -
        used by default in case of missing values.
        """

        if series is None:

            self._rainfall_series = None
            self._rainfall_series_mean = None

        elif isinstance(series, pd.Series):

            # to speed up fetching the data, we make a dictionary having the time as keys
            d = {(t.year,t.month,t.day): float(v) for t,v in series.iteritems()}

            self._rainfall_series = d
            self._rainfall_series_mean = float(series.mean())

        else:
            print(type(rseries))
            raise ValueError('Input a time-series.')

    @property
    def rainfall_series_mean(self):
        """ The all-time mean of the daily rainfall (mm/d). """
        if self._rainfall_series_mean:
            return self._rainfall_series_mean
        else:
            return self._rainfall_series_mean_


    #~~~~~~~~~~~~~~~~~~~

    @property
    def humidity(self):
        """ Humidity (%). """
        t = self._date_tuple
        s = self.humidity_series
        if (t and s) and (t in s):
            return s[t]
        else:
            return self.humidity_series_mean

    @humidity.setter
    def humidity(self, value):

        if isinstance(value, (int, float)):
            self._humidity_series_mean_ = value
        else:
            raise ValueError

    @property
    def humidity_series(self):
        """ Humidity (%) time series.

        A dict with a (year,day)-tuple keys and float values.
        """
        return self._humidity_series

    @humidity_series.setter
    def humidity_series(self,series):
        """ Sets the daily humidity time-series variable.

        Expects a date-time indexed time-series e.g.
        2007-01-01 00:00:00 - 12

        Furthermore, sets the all-time mean value -
        used by default in case of missing values.
        """

        if series is None:

            self._humidity_series = None
            self._humidity_series_mean = None

        elif isinstance(series, pd.Series):

            # to speed up fetching the data, we make a dictionary having the time as keys
            d = {(t.year,t.month,t.day): float(v) for t,v in series.iteritems()}

            self._humidity_series = d
            self._humidity_series_mean = float(series.mean())

        else:

            print(type(series))
            raise ValueError('Input a time-series.')

    @property
    def humidity_series_mean(self):
        """ The all-time mean of the mean-daily humidity (%). """
        if self._humidity_series_mean:
            return self._humidity_series_mean
        else:
            return self._humidity_series_mean_

    # --------------------------------

    @property
    def temperature(self):
        """ Temperature (deg C). """
        t = self._date_tuple
        s = self.temperature_series
        if (t and s) and (t in s):
            return s[t]
        else:
            return self.temperature_series_mean

    @temperature.setter
    def temperature(self, value):

        if isinstance(value, (int, float)):
            self._temperature_series_mean_ = value
        else:
            raise ValueError

    @property
    def temperature_series(self):
        """ Temperature (deg C) time series.

        A dict with a (year,day)-tuple keys and float values.
        """
        return self._temperature_series

    @temperature_series.setter
    def temperature_series(self,series):
        """ Sets the temperature time-series variable.

        Expects a date-time indexed time-series e.g.
        2007-01-01 00:00:00 - 12

        Furthermore, sets the all-time mean value -
        used by default in case of missing values.
        """

        if series is None:

            self._temperature_series = None
            self._temperature_series_mean = None

        elif isinstance(series, pd.Series):

            # to speed up fetching the data, we make a dictionary having the time as keys
            d = {(t.year,t.month,t.day): float(v) for t,v in series.iteritems()}

            self._temperature_series = d
            self._temperature_series_mean = float(series.mean())

        else:

            print(type(series))
            raise ValueError('Input a time-series.')

    @property
    def temperature_series_mean(self):
        """ The all-time mean of the mean-daily temperature (deg C). """
        if self._temperature_series_mean:
            return self._temperature_series_mean
        else:
            return self._temperature_series_mean_

# --------------------------------

    @property
    def windspeed(self):
        """ Windspeed (m/s). """
        t = self._date_tuple
        s = self.windspeed_series
        if (t and s) and (t in s):
            return s[t]
        else:
            return self.windspeed_series_mean

    @windspeed.setter
    def windspeed(self, value):

        if isinstance(value, (int, float)):
            self._windspeed_series_mean_ = value
        else:
            raise ValueError

    @property
    def windspeed_series(self):
        """ Windspeed (m/s) time series.

        A dict with a (year,day)-tuple keys and float values.
        """
        return self._windspeed_series

    @windspeed_series.setter
    def windspeed_series(self,series):
        """ Sets the wind speed time-series variable.

        Expects a date-time indexed time-series e.g.
        2007-01-01 00:00:00 - 12

        Furthermore, sets the all-time mean value -
        used by default in case of missing values.
        """

        if series is None:

            self._windspeed_series = None
            self._windspeed_series_mean = None

        elif isinstance(series, pd.Series):

            # to speed up fetching the data, we make a dictionary having the time as keys
            d = {(t.year,t.month,t.day): float(v) for t,v in series.iteritems()}

            self._windspeed_series = d
            self._windspeed_series_mean = float(series.mean())

        else:

            print(type(series))
            raise ValueError('Input a time-series.')

    @property
    def windspeed_series_mean(self):
        """ The all-time mean of the mean-daily wind speed (m/s). """
        if self._windspeed_series_mean:
            return self._windspeed_series_mean
        else:
            return self._windspeed_series_mean_

    # --------------------------------

    def _get_DOY(self):
        """ . """

        parent = self._palm

        if parent is None:
            return self._DOY_
        else:
            return parent.DOY

    @property
    def _latitude(self):
        """ . """

        parent = self._palm

        if parent is None:
            return self._latitude_
        else:
            return parent.latitude

    @property
    def radiation_extraterrestrial_daily(self):
        """ The solar irridiance just outside the atmosphere (MJ/m2/day).
        
        See page 31 of the 2004 book by Goudriaan and Van Laar, equation 3.7.

        """
        d = self.daylength
        a = self.sine_solar_height_mean
        b = self.sine_solar_height_amplitude

        # eccentricity factor
        ec = self.eccentricity_factor

        # reference solar irridiance
        S0 = self.parameters['solar_constant']['value']

        # daily integral of sine solar height
        int_sine_solar_height = a*d + (24*b/PI) * cos( (PI/2) * (d/12 -1) )

        # J -> MJ, hrs -> secs
        return 10**-6 * 3600 * S0 * int_sine_solar_height * ec

    def calc_sine_solar_height_mean(self):

        day = self._DOY
        gamma = self._latitude

        tilt = self.parameters['tilt_of_earth']['value']

        singamma = sin(rad(gamma))
        cosgamma = cos(rad(gamma))

        sindelta = -sin(rad(tilt))*cos(2*PI*(day+10)/self._palm._days_in_year)
        cosdelta = sqrt(1-sindelta**2)

        # the mean sine of the solar height [-1,1] - given the day, latitude
        # the height at 6AM and 6PM.
        # for the Netherlands varies from -.31 (Dec 21st) to .31 (June 21st)
        a = singamma*sindelta

        assert a <= 1
        assert a >= -1

        return a

    def calc_sine_solar_height_amplitude(self):

        day = self._DOY
        gamma = self._latitude

        tilt = self.parameters['tilt_of_earth']['value']

        singamma = sin(rad(gamma))
        cosgamma = cos(rad(gamma))

        sindelta = -sin(rad(tilt))*cos(2*PI*(day+10)/self._palm._days_in_year)
        cosdelta = sqrt(1-sindelta**2)

        # the amplitude - idem [0,1]
        # for the Netherlands varies very little, approx equal to .6.
        b = cosgamma*cosdelta

        assert b >= 0
        assert b <= 1

        return b

    @property
    def eccentricity_factor(self):
        ''' A factor describing the eccentricity around the earth'

        See page 31 of the 2004 book by Goudriaan and Van Laar, equation 3.1b'''

        day = self._DOY

        return 1 + 0.033*cos(2*PI*(day - 10)/self._palm._days_in_year)


    def calc_radiation_extraterrestrial(self, hour=12):
        """ The solar irridiance just outside the atmosphere (J/m2/s), at a given hour (the
        middle of the day). 
        
        Based on the book by Goudriaan and Van Laar, 2004, on crop modelling p.29,  
        equation 3.2.
        
        """

        # reference solar irridiance
        S0 = self.parameters['solar_constant']['value']

        sinb = self.calc_sine_solar_height(hour)

        # the last factor takes into account the
        # earths eccentric trajectory around the sun
        earth_eccentricity = self.eccentricity_factor

        S = S0 * sinb * earth_eccentricity

        assert S >= 0

        return S

    def calc_sine_solar_height(self, hour=12):
        ''' Gives the height of the sun at a given hour'''

        a = self.sine_solar_height_mean
        b = self.sine_solar_height_amplitude

        # the height of the sun
        sinb = a + b*cos(2*PI*(hour-12)/24)

        if sinb < 0:
            sinb = 0

        return sinb

    def calc_PAR(self, hour=12):

        T = self.transmission_factor

        I0 = self.calc_radiation_extraterrestrial(hour=hour)

        c = self.parameters['PAR_fraction']['value']

        return c*T*I0

    @property
    def daylength(self):
        ''' Calculates the length of the day (h)'''
        res =  self.hour_of_dusk - self.hour_of_dawn

        assert res >= 0

        return res

    @property
    def hour_of_dusk(self):
        ''' Gives the hour at which the sun goes down'''

        a = self.sine_solar_height_mean
        b = self.sine_solar_height_amplitude

        return 12*(2-acos(a/b)/PI)

    @property
    def hour_of_dawn(self):
        ''' Gives the hour at which the sun comes up'''
        a = self.sine_solar_height_mean
        b = self.sine_solar_height_amplitude

        return 12*(acos(a/b)/PI)

    def calc_fraction_diffuse_lower_limit(self,hour=12):
        """ A lower limit on the fraction of diffuse light (1).
        
        Source: Goudriaan en van Laar
        """

        sinb = self.calc_sine_solar_height(hour)

        if sinb > 0:
            return 0.15 + 0.85 * (1 - exp(-0.1/sinb))
        else:
            return 0

    def calc_fraction_diffuse(self, hour=12):
        """ The fraction of diffuse light at a certain hour (1). """
        return max(self.fraction_diffuse, self.calc_fraction_diffuse_lower_limit(hour=hour))

    @property
    def fraction_diffuse(self):
        """ The daily average fraction of diffuse light (1).
        
        Uses some emperical relation. Source: De Jong, J. B. R. M. (1980). 
        Een karakterisering van de zonnestraling in Nederland.
        """

        f = self.transmission_factor

        if f < 0.07:
            res =  1.
        elif f >= 0.07 and f < 0.35:
            res = 1.-2.3*(f-0.07)**2
        elif f >= 0.35 and f < 0.75:
            res = 1.33-1.46*f
        else:
            res = 0.23

        assert res <= 1
        assert res >= 0

        return res

    @property
    def transmission_factor(self):
        """ (1) """

        I = self.radiation
        Iext = self.radiation_extraterrestrial_daily

        return I/Iext

    @property
    def canopy_net_radiation_capture_reference(self):
        """ The net radiation received by the canopy surface of a reference crop (MJ/m2/day). """

        albedo = self.parameters['crop_reference_albedo']['value']

        # short and longwave
        I_sun = self.radiation

        # longwave
        I_sky = self.radiation_longwave_sky_daily
        I_earth = self._radiation_longwave_earth_daily

        return (1 - albedo) * I_sun + I_sky - I_earth

    @property
    def canopy_net_radiation_capture(self):
        """ The net radiation received by the canopy surface (MJ/m2/day). """

        albedo = self.parameters['albedo']['value']

        # short and longwave
        I_sun = self.radiation

        # longwave
        I_sky = self.radiation_longwave_sky_daily
        I_earth = self._radiation_longwave_earth_daily

        return (1 - albedo) * I_sun + I_sky - I_earth


    @property
    def relative_humidity(self):
        """ The humidity in percentage converted to a fraction (1). """

        return 0.01*self.humidity

    @property
    def ET_potential(self):
        """ (mm/day).
        
        Calculated as prescribed by the FAO.
        See http://www.fao.org/docrep/X0490E/x0490e06.htm .
        """

        Rn = self.canopy_net_radiation_capture_reference
        VPD = self.vapour_pressure_deficit
        T = self.temperature

        c_psy = self.parameters['psychrometer_coefficient']['value']
        c_ratio_molecular_weight = self.parameters['ratio_molecular_weight']['value']
        c_specific_gas_constant = self.parameters['specific_gas_constant']['value']
        c_latent_heat = self.parameters['latent_heat_water']['value']

        aerodynamic_resistance = self.aerodynamic_resistance
        bulk_surface_resistance = self.bulk_surface_resistance
        slope = self.saturated_vapour_pressure_slope

        virtual_temperature = 1.01*(T + 273.16)
        specific_heat_moist_air_times_mean_air_density = (c_psy*c_ratio_molecular_weight*c_latent_heat)/(virtual_temperature*c_specific_gas_constant)

        num = slope*Rn+specific_heat_moist_air_times_mean_air_density*(VPD/aerodynamic_resistance)
        denum = slope +c_psy*(1+(bulk_surface_resistance/aerodynamic_resistance))

        ET = num/denum

        ET_mm =  ET/c_latent_heat

        return ET_mm

    @property
    def aerodynamic_resistance(self):
        """ The aerodynamic resistance of the reference crop grass (s/m)"""

        u = self.windspeed

        c_reference_height = self.parameters['crop_reference_height']['value']
        c_reference_surface_resistance = self.parameters['crop_reference_surface_resistance']['value']
        c_karman_constant = self.parameters['karman_constant']['value']

        displacement_height = 2/3*c_reference_height  # Abtew 1989
        roughness_length_momentum = 0.123 * c_reference_height
        roughness_length_heat = 0.1 * roughness_length_momentum

        height_of_measurement = 2   #m

        num_aer_res = log((height_of_measurement-displacement_height)/roughness_length_momentum)*log((height_of_measurement-displacement_height)/roughness_length_heat)
        denum_aer_res = (c_karman_constant)**2*u
        aer_res = num_aer_res/denum_aer_res

        return aer_res

    @property
    def bulk_surface_resistance(self):
        """ The aerodynamic resistance of the reference crop grass (s/m)"""

        c_reference_height = self.parameters['crop_reference_height']['value']
        c_reference_stomatal_resistance = self.parameters['crop_reference_stomatal_resistance']['value']

        LAI_grass = 24 * c_reference_height
        LAI_active = 0.5 * LAI_grass
        bulk_surf_res = c_reference_stomatal_resistance/(LAI_active)

        return bulk_surf_res

    @property
    def _radiation_longwave_earth(self):
        """ The (long-wave) radiation given off by the earth (J/m2/s). """

        T_avg = self.temperature

        sigma = self.parameters['sigma']['value']

        # 0 deg C -> Kelvin
        T0 = 273.16

        T = T_avg + T0

        # Stefan-Boltzmann
        I = sigma*T**4

        return I

    @property
    def _radiation_longwave_earth_daily(self):
        """ The (long-wave) radiation given off by the earth (MJ/m2/day). """

        I = self._radiation_longwave_earth

        # seconds per day
        SPD = SECONDS_PER_DAY

        return 10**-6 * SPD * I

    @property
    def _radiation_longwave_sky(self):
        """ The (long-wave) radiation given off by the sky (J/m2/s).
        
        Involves the use of an adapted Swinbank formula - see p. 7 of
        https://library.wur.nl/WebQuery/wurpubs/fulltext/4413
        
        """

        # note, should be in the range [0,a0]
        a = self.transmission_factor
        T_avg = self.temperature
        I_earth = self._radiation_longwave_earth

        # reference transmission factor
        a0 = self.parameters['reference_transmission_factor']['value']

        # The estimated radiation given off by the sky in case
        # it was a perfect black-body radiator (balance)
        I_sky_BB = I_earth

        # Swinbank constant - see the original paper by Swinbank, 1963.
        c_swinbank = self.parameters['swinbank_constant']['value']

        # 0 deg C -> Kelvin
        T0 = 273.16
        T = T_avg + T0

        # Adapted Swinbank formula:
        # a linear combination via a of the clear-skies Swinbank estimate
        # and the black-body sky estimate

        radiation_longwave_sky = (a/a0) * c_swinbank * T**6 + ((a0 - a)/a0) * I_sky_BB

        # a = 0 -> I_sky_BB
        # a = a0 -> Swinbank
        return radiation_longwave_sky

    @property
    def radiation_longwave_sky_daily(self):
        """ The (long-wave) radiation given off by the sky (MJ/m2/day). """

        I = self._radiation_longwave_sky

        # seconds per day
        SPD = SECONDS_PER_DAY

        return 10**-6 * SPD * I

    @property
    def vapour_pressure_early_morning(self):
        """ . """

        VPref = self.saturated_vapour_pressure
        rH = self.relative_humidity

        return rH*VPref

    @property
    def vapour_pressure_deficit(self):
        """ (kPa) """

        VPa = self.vapour_pressure_early_morning
        VPref = self.saturated_vapour_pressure

        return VPref - VPa

    @property
    def saturated_vapour_pressure(self):
        """ The satured vapour pressure (kPa).
        
         Is derived from the (daily average) temperature (deg C).

         The Teten's formula, which is an emperical expression for saturation 
         vapour pressure with respect to liquid water that includes the variation
         of letent heat with temperature   

         Tetens, O. (1930). Uber einige meteorologische Begriffe. Z. geophys, 6, 297-309.
        """

        c_e_zero = 0.610588 # kPa
        c_b = 17.32491 # kPa
        c_T_one = 273.16 # kPa
        c_T_two = 35.86 # kPa

        T = self.temperature

        VPS = c_e_zero*exp(c_b*T/(T+c_T_one-c_T_two))

        return VPS

    @property
    def saturated_vapour_pressure_slope(self):
        """ The change of the satured vapour pressure with temperature (kPa/C).

         Is derived from the (daily average) temperature (deg C).

         The Teten's formula, which is an emperical expression for saturation 
         vapour pressure with respect to liquid water that includes the variation
         of letent heat with temperature   

         Tetens, O. (1930). Uber einige meteorologische Begriffe. Z. geophys, 6, 297-309.     
        """

        T = self.temperature # deg C
        VPS = self.saturated_vapour_pressure # kPa

        c_b = 17.32491 # kPa
        c_T_one = 273.16 # kPa
        c_T_two = 35.86 # kPa

        slope = (c_T_one-c_T_two)*c_b*VPS/(T+(c_T_one-c_T_two))**2

        return slope
