#!/usr/bin/env python
''' Provides the trunk modelling. '''

import yaml

from .helpers import add_dumps
from .helpers import Spline

from math import exp


@add_dumps
class Trunk(object):
    ''' Trunk related logic.

    The instance of this class (singleton design pattern)
    "the trunk" models a hectare of oil palm trunks.

    Main variable:
        trunk mass

    Main parameters:
        potential growth rate vs YAP

    Notes
    -----
    The potential growth rate determines the sink strength
    which again determines the assimilats for mass growth.
    - see the reference below.

    Mass loss is taken to be zero at all times.

    References
    ----------
    Corley, R.H.V. and Gray, B.S. and Siew Kee, NG, 1971.
    Productivity of the oil palm in Malaysia.
    '''

    parameters = yaml.load('''

    density_a:
        value: 7.62
        unit: 'kg//m3/year'
        info: 'Change in density with palm age.'
        source: Corley, R. H. V., Hardon, J. J., & Tan, G. Y. (1971). Analysis of growth of the oil
                palm (Elaeis guineensis Jacq.) I. Estimation of growth parameters and application in
                breeding. Euphytica, 20(2), 307-315.

    density_b:
        value: 83
        unit: 'kg/m3'
        info: 'Initial trunk density at planting'
        source: Corley, R. H. V., Hardon, J. J., & Tan, G. Y. (1971). Analysis of growth of the oil
                palm (Elaeis guineensis Jacq.) I. Estimation of growth parameters and application in
                breeding. Euphytica, 20(2), 307-315.

    specific_maintenance:
        value: 0.0005
        unit: 'g_CH2O/g_DM/day'
        info: 'The specific maintenance.'
        source: 'Copied from Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et
                 productivite du palmier a huile en liaison avec les facteurs climatiques.
                 Table II.'

    conversion_efficiency:
        value: 0.69
        unit: 'g_DM/g_CH2O'
        info: 'The conversion efficiency.'
        source: 'Copied from Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et
                 productivite du palmier a huile en liaison avec les facteurs climatiques. In
                 turn based on van Kraalingen, D.W.G., 1989. See text below table II and table III.'

    lignification_rate:
        value: 0.74
        unit: 'kg/m3/month'
        info: 'The lignification rate.'
        source: 'Corley, R.H.V. and P.B. Tinker. 2003b. Growth, flowering and yield. In
                The Oil Palm 4th Edn. B.S. Ltd. Blackwell Publishing, pp 89–131.'

    mass_loss_rate:
        value: 0.0
        unit: 't/ha/day'
        info: 'The mass loss rate.'
        source: 'Assumption: the trunk loses no mass --- first made by Alba/Hoffman.'

    potential_growth_rates:
        value: [[0, 1.6],
                 [3, 9.5],
                 [6, 19.6],
                 [9, 22.8],
                 [12, 19.2],
                 [15, 13.5],
                 [18, 8.6],
                 [21, 5.2],
                 [24, 3.0],
                 [27, 1.7]]
        unit: 'kg DM/palm/year'
        info: 'The potential growth rate at different points in time, determines the 
                potential sink strength and thus assimilate partitioning.'
        source: 'Obtained by fitting a Gompertz function to the mass reported in Corley, R.H.V.
                 and Gray, B.S. and Siew Kee, NG, 1971. Productivity of the oil palm in Malaysia.'

    ''',
                           Loader=yaml.SafeLoader)

    initial_values = yaml.load('''

    mass:
        value: 0.1
        unit: 'kg_DM/plant'
        info: 'Trunk mass at 0 MAP.'
        source: 'Amir, H. G., Shamsuddin, Z. H., Halimi, M. S., Marziah, M., & Ramlan,
                 M. F. (2005). Enhancement in nutrient accumulation and growth of oil
                 palm seedlings caused by PGPR under field nursery conditions.
                 Communications in soil science and plant analysis, 36(15-16), 2059-2066.'

    ''',
                               Loader=yaml.SafeLoader)

    units = {
        'assim_growth': 'kg_CH2O/ha/day',
        'density': 'kg/m3',
        'lignified_mass': 'kg',
        'lignified_mass_change_rate': 'kg_DM/ha/day',
        'maintenance_requirement': 'kg_CH2O/ha/day',
        'mass': 'kg_DM/ha',
        'mass_change_rate': 'kg_DM/ha/day',
        'mass_change_rate_yearly': 'kg_DM/ha/year',
        'mass_growth_rate': 'kg_DM/ha/day',
        'mass_loss_rate': 'kg_DM/ha/day',
        'potential_growth_actual': 'kg_DM/ha/day',
        'potential_growth_rate': 'kg_DM/ha/day',
        'potential_growth_rate_per_palm': 'kg_DM/palm/year',
        'potential_sink_strength': 'kg_CH2O/ha/day',
        'volume': 'm3'
    }

    _prefix = 'trunk'

    def __init__(self, palm=None):

        self._palm = palm

        # convert from kg/plant -> ton/ha
        mass_per_palm = self.initial_values['mass']['value']
        self.mass = self._planting_density * mass_per_palm
        self.lignified_mass = 0

        # convert potential growth rate values (pgr) to a pgr function
        # - a (cubic: k=3) spline
        pgrs = self.parameters['potential_growth_rates']['value']
        self._potential_growth_rate_spline = Spline(pgrs, k=3)

        # only used for testing - e.g. to see that the trunks grow
        # when supplied with assimilates
        self._assim_growth_ = 0

    #~~~~~~~~~~~~~~

    @property
    def _planting_density(self):
        ''' Planting density (1/ha). '''
        return self._palm.planting_density

    @property
    def _YAP(self):
        ''' Years after planting (year). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.YAP

    #~~~~~~~~~~~~~~~~

    def update(self, dt=1):
        ''' Update state by dt days.'''

        self.lignified_mass += self.lignified_mass_change_rate * dt
        self.mass += self.mass_change_rate * dt

        assert self.mass >= 0
        assert self.lignified_mass > 0

    #~~~~~~~~~~~~~~~~

    @property
    def mass_change_rate(self):
        ''' Mass change rate (kg_DM/ha/day). '''

        return self.mass_growth_rate - self.mass_loss_rate

    @property
    def mass_growth_rate(self):
        ''' Mass change rate (kg_DM/ha/day). '''

        c = self.parameters['conversion_efficiency']['value']

        return c * self.assim_growth

    @property
    def mass_loss_rate(self):
        ''' Mass loss rate (kg_DM/ha/day)'''

        return self.parameters['mass_loss_rate']['value']

    @property
    def mass_change_rate_yearly(self):
        ''' Mass change rate (kg_DM/ha/year). '''

        return self._palm._days_in_year * self.mass_change_rate

    @property
    def potential_growth_actual(self):
        ''' Actual growth : potential growth (1). '''

        return self.mass_growth_rate / self.potential_growth_rate

    #~~~~~~~~~~~~~~~

    @property
    def potential_growth_rate_per_palm(self):
        ''' Potential growth rate (kg_DM/palm/year). '''

        YAP = self._YAP

        yearly_rate = self._potential_growth_rate_spline.calc(YAP)

        return yearly_rate

    @property
    def potential_growth_rate(self):
        ''' Potential growth rate (kg_DM/ha/day). '''

        yearly_per_palm = self.potential_growth_rate_per_palm

        c = (1 / self._palm._days_in_year)

        return max(0, c * self._planting_density * yearly_per_palm)

    @property
    def potential_sink_strength(self):
        ''' Potential sink strength (kg_CH2O/ha/day). '''

        c = self.parameters['conversion_efficiency']['value']

        return self.potential_growth_rate / c

    @property
    def assim_growth(self):
        ''' Assimilates for growth (kg_CH2O/ha/day). '''

        if self._palm is None:
            return self._assim_growth_
        else:
            return self._palm.assimilates.assim_growth_trunk

    #~~~~~~~~~~~~

    @property
    def maintenance_requirement(self):
        ''' Maintenance requirement (kg_CH2O/ha/day). '''

        c = self.parameters['specific_maintenance']['value']

        x = self.mass

        active_mass = x - self.lignified_mass

        res = c * active_mass

        return res

    @property
    def density(self):
        ''' Trunk density (kg/m3)'''

        a = self.parameters['density_a']['value']
        b = self.parameters['density_b']['value']

        d = a * self._YAP + b

        return d

    @property
    def volume(self):
        '''The trunk volume (m3). '''

        V = self.mass / self.density

        return V

    @property
    def lignified_mass_change_rate(self):
        '''The change rate of the lignified mass of the trunk (kg/day)'''

        c = self.parameters['lignification_rate']['value']

        rate = self.volume * (c / self._palm._days_in_month)

        return rate