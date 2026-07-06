#!/usr/bin/env python
''' Provides the soil-water balance models. '''

import yaml

from math import exp
from .helpers import add_dumps


class PTF(object):
    """ Translates a soil texture string to volumetric water contents; a PTF.
    
    Implements the translation rules of [1], uses a Van Genuchten methodology.
    
    Examples
    --------
    
    ptf = PTF('Sand')
    
    Fetch shaping parameter (1/kPa)
    
    >>> ptf.alpha
    0.38
    
    Fetch plant available water content (m3/m3)
    
    >>> ptf.PAWC
    0.2
    
    References
    ----------
    [1] Hodnett, Martin & Tomasella, Javier. (2002).
        Marked differences between van Genuchten soil water-retention
        parameters for temperate and tropical soils:
        A new water-retention pedo-transfer functions developed for tropical soils.
        Geoderma. 108. 155-180. 10.1016/S0016-7061(02)00105-2. 

    """

    parameter_library = yaml.load("""
    
    sand:
        alpha: 0.380
        n: 2.474
        saturated_moisture_content: 0.410
        residual_moisture_content: 0.037
    loamy sand:
        alpha: 0.837
        n: 1.672
        saturated_moisture_content: 0.438
        residual_moisture_content: 0.062
    sandy loam:
        alpha: 0.396
        n: 1.553
        saturated_moisture_content: 0.461
        residual_moisture_content: 0.111
    loam:
        alpha: 0.246
        n: 1.461
        saturated_moisture_content: 0.521
        residual_moisture_content: 0.155
    silty loam:
        alpha: 0.191
        n: 1.644
        saturated_moisture_content: 0.601
        residual_moisture_content: 0.223
    sandy clay loam:
        alpha: 0.644
        n: 1.535
        saturated_moisture_content: 0.413
        residual_moisture_content: 0.149
    clay loam:
        alpha:  0.392
        n: 1.437
        saturated_moisture_content: 0.519
        residual_moisture_content: 0.226
    silty clay loam:
        alpha: 0.298
        n: 1.513
        saturated_moisture_content: 0.586
        residual_moisture_content: 0.267
    silty clay:
        alpha:  0.258
        n: 1.466
        saturated_moisture_content: 0.570
        residual_moisture_content: 0.278
    sandy clay:
        alpha:  0.509
        n: 1.396
        saturated_moisture_content: 0.460
        residual_moisture_content: 0.199
    clay:
        alpha: 0.463
        n: 1.514
        saturated_moisture_content: 0.546
        residual_moisture_content: 0.267
    
    """,
                                  Loader=yaml.SafeLoader)

    def __init__(self, texture_class='sand'):

        self.texture_class = texture_class

    @property
    def options(self):
        return list(self.parameter_library)

    @property
    def parameters(self):
        """ Parameters (dict) associated with a certain texture class. """
        key = self.texture_class
        library = self.parameter_library

        return library[key]

    @property
    def alpha(self):
        """  (1/kPa) """
        return self.parameters['alpha']

    @property
    def n(self):
        """ (1) """
        return self.parameters['n']

    @property
    def m(self):
        """ (1) """
        return 1. - 1. / self.n

    @property
    def saturated_moisture_content(self):
        """ (m3/m3) """
        return self.parameters['saturated_moisture_content']

    @property
    def residual_moisture_content(self):
        """ (m3/m3) """
        return self.parameters['residual_moisture_content']

    def calc_water_content(self, pressure):
        """ Returns the volumetric water content at a certain suction pressure (m3/m3) """

        a = self.alpha
        n = self.n

        sat = self.saturated_moisture_content
        res = self.residual_moisture_content

        m = 1. - 1. / n

        num = sat - res
        denum = (1 + (a * pressure)**n)**m

        water_content = res + num / denum

        return water_content

    @property
    def water_content_FC(self):
        """ the volumetric water content (m3/m3) at -10 kPa  """

        # reference pressures - matrix potential (kPa)
        P_ref = 10

        return self.calc_water_content(pressure=P_ref)

    @property
    def water_content_PWP(self):
        """ the volumetric water content (m3/m3) at -1500 kPa  """

        # reference pressures - matrix potential (kPa)
        P_ref = 1500

        return self.calc_water_content(pressure=P_ref)

    @property
    def plant_available_water_content(self):
        """ The plant available volumetric water content (m3/m3).
        
        Defined as the difference in water content at
        field capacity (-33 kPa) and at the permanent wilting point (-1500 kPa).
        """

        return self.water_content_FC - self.water_content_PWP


@add_dumps
class Soil(object):
    ''' '''

    parameters = yaml.load('''

    default_water_holding_capacity:
        value: 500.
        unit: 'mm'
        info: 'Working definition: The difference between rooting zone water content at 
                field capacity (pF 2) and permanent wilting point (pF 4.2). If soil texture
                and rooting depth are not given.'
        source: 'Input: soil/root characteristic.'

    relative_evapotranspiration_a:
        value: 0.2
        unit: '1'
        info: 'Shapes the sigmoid (1/(1+exp(-(x-a)/b))) relation between actual to potential 
                ET_monthly versus soil water content.'
        source: 'Based on the relation given in Combres et al. 2013 which refers to the PhD
                 thesis by E. Dufrene (1989).'

    relative_evapotranspiration_b:
        value: 0.1
        unit: '1'
        info: 'Shapes the sigmoid (1/(1+exp(-(x-a)/b))) relation between actual to potential 
                ET_monthly versus soil water content.'
        source: 'Based on the relation given in Combres et al. 2013 which refers to the PhD
                thesis by E. Dufrene (1989).'
    ''',
                           Loader=yaml.SafeLoader)

    units = {
        'available_water': 'mm',
        'available_water_change_rate': 'mm/day',
        'drainage': 'mm/day',
        'evaporation': 'mm/day',
        'evapotranspiration': 'mm/day',
        'evapotranspiration_potential': 'mm/day',
        'moisture_content': '1',
        'rainfall': 'mm/day',
        'relative_evaporation': '1',
        'relative_evapotranspiration': '1',
        'relative_potential_evaporation': '1',
        'relative_potential_transpiration': '1',
        'relative_transpiration': '1',
        'soil_depth': 'm',
        'transpiration': 'mm/day',
        'transpiration_reduction': '1',
        'water_deficit': 'mm',
        'water_holding_capacity': 'mm'
    }

    _prefix = 'soil'

    def __init__(self, palm=None, soil_depth=None, soil_texture_class=None):

        self._palm = palm

        self.soil_depth = soil_depth
        self.soil_texture_class = soil_texture_class

        # It is assumed that the soil has FC soil moisture content at planting.
        self.available_water = self.water_holding_capacity

        # implemented for proto-typing purposes. See associated properties.
        self._rainfall_ = 120

    #~~~~~~~~~~~~~~~~

    @property
    def _weather(self):
        ''' A reference to the weather. '''
        if self._palm is None:
            return None
        else:
            return self._palm.weather

    @property
    def rainfall(self):
        ''' Rainfall (mm/day). '''
        if self._weather is None:
            return self._rainfall_
        else:
            return self._weather.rainfall

    #----------------

    @property
    def soil_texture_class_options(self):
        """ List of soil texture class options. """
        return PTF.options

    @property
    def soil_texture_class(self):
        """ Soil texture class eg silty clay, sandy loam. """
        return self._soil_texture_class

    @soil_texture_class.setter
    def soil_texture_class(self, soil_texture_class):
        """ Sets the soil texture class eg silty clay, sandy loam. """

        # eg sandy loam, silty clay
        self._soil_texture_class = soil_texture_class

        # the associated pedo-transfer-function
        ptf = PTF(soil_texture_class)

        # m3/m3
        self._plant_available_water_content = ptf.plant_available_water_content

    #~~~~~~~~~~~~~~~~

    @property
    def water_holding_capacity(self):
        '''The water holding capacity of soil in the rooting zone (mm).

        The amount of water freed when moving
        from the water holding capacity
        to the permanent wilting point.
        '''

        if self.soil_depth is not None:

            c = self._plant_available_water_content
            d = self.soil_depth

            # m --> mm via x1000
            return 1000 * c * d

        else:

            return self.parameters['default_water_holding_capacity']['value']

    @property
    def moisture_content(self):
        ''' The available water : water holding capacity ratio (1). '''
        AW = self.available_water
        AWC = self.water_holding_capacity

        return AW / AWC

    #~~~~~~~~~~~~~~~~

    def update(self, dt=1):
        ''' Update by dt days. '''

        for i in range(dt):
            self._update(dt=1)

    def _update(self, dt=1):
        ''' Update by dt days. '''

        self.available_water += self.available_water_change_rate * dt

    #~~~~~~~~~~~~~~~~

    @property
    def available_water_change_rate(self):
        ''' Rate with which the water held changes (mm/day).

        Follows from the sum of rainfall_monthly (P),
        ET_monthly (ET) and drainage_monthly (D):

            d/dt(AW) = P - ET - D
        '''

        P = self.rainfall
        ET = self.evapotranspiration
        D = self.drainage

        return P - ET - D

    #~~~~~~~~~~~~~~~~

    @property
    def evapotranspiration(self):
        ''' Actual evapotransipiration (ET) rate (mm/day). '''
        return self.relative_evapotranspiration * self.evapotranspiration_potential

    @property
    def transpiration(self):
        ''' Actual transpiration (T) rate (mm/day). '''
        return self.relative_transpiration * self.evapotranspiration_potential

    @property
    def evaporation(self):
        ''' Actual evaporation (E) rate (mm/day)'''
        return self.evapotranspiration - self.transpiration

    @property
    def relative_transpiration(self):
        ''' The relative transpiration rate (1).

        A value of 1 corresponds to potential transpiration.
        A (extreme) value of 0 corresponds to no transpiration.
        '''

        fraction_potential_transpiration = self.relative_potential_transpiration

        fraction_T = self.relative_evapotranspiration * fraction_potential_transpiration

        assert fraction_T >= 0

        return fraction_T

    @property
    def relative_potential_transpiration(self):
        '''Potential transiration fraction'''

        fraction_E_WP = self.calc_relative_evapotranspiration(rel_AW=0)

        fraction_intercepted = self._palm.fronds.fraction_intercepted

        potential_T_rate = (1 - fraction_E_WP) * fraction_intercepted

        return potential_T_rate

    @property
    def transpiration_reduction(self):
        '''Transpiration reduction function'''

        trans_reduction = self.relative_transpiration / self.relative_potential_transpiration

        assert trans_reduction > 0
        assert trans_reduction <= 1

        return trans_reduction

    @property
    def relative_potential_evaporation(self):
        ''' The relative evaporation fraction (1).

        A value of 1 corresponds to potential transpiration.
        A (extreme) value of 0 corresponds to no transpiration.
        '''
        relative_Tpot = self.relative_potential_transpiration

        return 1 - relative_Tpot

    @property
    def relative_evaporation(self):
        ''' The relative transpiration rate (1).

        A value of 1 corresponds to potential transpiration.
        A (extreme) value of 0 corresponds to no transpiration.
        '''
        relative_transpiration = self.relative_transpiration

        return self.relative_evapotranspiration - relative_transpiration

    @property
    def relative_evapotranspiration(self):
        ''' The relative transpiration rate (1).

        A value of 1 corresponds to potential transpiration.
        A (extreme) value of 0 corresponds to no transpiration.
        '''

        rel_AW = self.moisture_content

        return self.calc_relative_evapotranspiration(rel_AW)

    def calc_relative_evapotranspiration(self, rel_AW):
        ''' The relative transpiration rate (1).

        A value of 1 corresponds to potential transpiration.
        A (extreme) value of 0 corresponds to no transpiration.
        '''

        a = self.parameters['relative_evapotranspiration_a']['value']
        b = self.parameters['relative_evapotranspiration_b']['value']

        # ET reduces with rel. lack of AW
        return 1 / (1 + exp(-(rel_AW - a) / b))

    @property
    def drainage(self):
        ''' Drainage rate (mm/day).

        Here taken broadly as any process bringing the
        water level to the water holding capacity:
        run-off, percolation, etc.
        '''

        AW = self.available_water
        P = self.rainfall
        ET = self.evapotranspiration

        AW_potential = AW + (P - ET)

        AWC = self.water_holding_capacity

        # any AW > AWC := drainage
        D_potential = AW_potential - AWC

        # D >= 0
        return max(0., D_potential)

    #~~~~~~~~~~~~

    @property
    def water_deficit(self):
        ''' The water deficit (mm).

        Follows by subtracting the available water (mm) from the
        the soil water holding capacity (mm).
        '''

        return max(0., self.water_holding_capacity - self.available_water)

    @property
    def evapotranspiration_potential(self):
        """ Collects the potential daily evapotranspiration of the weather component."""

        parent = self._weather

        if parent is None:
            return 0
        else:
            return parent.ET_potential