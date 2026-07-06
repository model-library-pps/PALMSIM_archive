#!/usr/bin/env python
''' Contains the root modelling. '''

import yaml

from .helpers import add_dumps
from .helpers import Spline
''' Provides the roots modelling. '''
@add_dumps
class Roots(object):
    ''' A class which models a field of roots.

    Main instance variables:
        - mass

    Note, mass determines the maintenance requirement.

    Main parameters:
        potential growth rates

    The potential growth rate determines the sink strenght which
    determines the assimilats for mass growth.

    Note, as an ad hoc assumption, mass loss/turnover is a fraction
    of the standing mass plus a constant rate.
    '''

    parameters = yaml.load('''

    conversion_efficiency:
        value: 0.69
        unit: 'g_DM/g_CH2O'
        info: 'The conversion efficiency.'
        source: 'Taken from Dufrene, E. and Ochs, R. and Saugier, B., 1990.
                    Photosynthese et productivite du palmier a huile en liaison
                    avec les facteurs climatiques.
                    In turn based on van Kraalingen, D.W.G., 1989.
                    See text below table II and table III.'
        uncertainty: 10%

    loss_param:
        value: 0.000582
        unit: '1/day'
        info: 'Co-determines the mass loss rate of the roots.'
        source: 'Henson, I. E. (2005). Modelling vegetative dry matter production
                 of oil palm. Oil Palm Bulletin, 52, 25.'
        uncertainty: 20%

    potential_growth_rates:
        value: [[0, 3.5],
                [3, 5.7],
                [6, 5.1],
                [9, 3.4],
                [12, 1.9],
                [15, 1.0],
                [18, 0.5],
                [21, 0.3],
                [24, 0.1],
                [27, 0.1]]
        unit: 'YAP, kg/palm/year'
        info: 'The potential growth rate at different points in time, determines the
                potential sink strength and thus assimilate partitioning.'
        source: 'Obtained by fitting a Gompertz function to the mass reported in Corley,
                R.H.V. and Gray, B.S. and Siew Kee, NG, 1971. Productivity of the oil palm in Malaysia.'
        uncertainty: 10%

    specific_maintenance:
        value: 0.0022
        unit: 'g_CH2O/g_DM/day'
        info: 'The specific maintenance.'
        source: 'Taken from Dufrene, E. and Ochs, R. and Saugier, B., 1990.
                Photosynthese et productivite du palmier a huile en liaison
                avec les facteurs climatiques.
                Table 2.'
        uncertainty: 20%

    ''',
                           Loader=yaml.SafeLoader)

    initial_values = yaml.load('''

        mass:
            value: 0.1
            uncertainty: 20%
            unit: 'kg_DM/palm'
            info: 'Initial weight of the plant part.'
            source: 'Amir, H. G., Shamsuddin, Z. H., Halimi, M. S., Marziah, M., & Ramlan,
                 M. F. (2005). Enhancement in nutrient accumulation and growth of oil
                 palm seedlings caused by PGPR under field nursery conditions.
                 Communications in soil science and plant analysis, 36(15-16), 2059-2066.'
    ''',
                               Loader=yaml.SafeLoader)

    units = yaml.load('''

        assim_growth                      : 'kg_CH2O/ha/day'
        maintenance_requirement           : 'kg_CH2O/ha/day'
        mass                              : 'kg_DM/ha'
        mass_change_rate                  : 'kg_DM/ha/day'
        mass_change_rate_yearly           : 'kg_DM/ha/year'
        mass_growth_rate                  : 'kg_DM/ha/day'
        mass_loss_rate                    : 'kg_DM/ha/day'
        mass_per_palm                     : 'kg_DM/palm'
        potential_growth_rate             : 'kg_DM/ha/day'
        potential_growth_rate_per_palm    : 'kg_DM/palm/year'
        potential_growth_realization      : '1'
        potential_sink_strength           : 'kg_CH2O/ha/day'

    ''',
                      Loader=yaml.SafeLoader)

    _prefix = 'roots'

    _log = []

    def __init__(self, palm=None):

        self._palm = palm

        # convert from kg/plant -> ton/ha
        mass_per_palm = self.initial_values['mass']['value']
        self.mass = self._planting_density * mass_per_palm

        # convert potential growth rate values (pgr) to a pgr function
        # - a (cubic: k=3) spline
        pgrs = self.parameters['potential_growth_rates']['value']
        self._potential_growth_rate_spline = Spline(pgrs, k=3)

        # only used for testing - e.g. to see if the roots grow
        # when supplied with assimilates.
        self._assim_growth_ = 0

    #~~~~~~~~~~~~~~

    @property
    def _YAP(self):
        ''' Years after planting (year). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.YAP

    @property
    def _planting_density(self):
        return self._palm.planting_density

    #~~~~~~~~~~~~~~~~

    def update(self, dt=1):
        ''' Update state by dt days.'''

        self.mass += self.mass_change_rate * dt

        assert self.mass >= 0

    @property
    def mass_change_rate(self):
        ''' Mass change rate (kg_DM/ha/day). '''

        return self.mass_growth_rate - self.mass_loss_rate

    @property
    def mass_change_rate_yearly(self):
        ''' Mass change rate (kg_DM/ha/year). '''

        return self._palm._days_in_year * self.mass_change_rate

    @property
    def potential_growth_realization(self):
        ''' Actual growth : potential growth (1). '''

        return self.mass_growth_rate / self.potential_growth_rate

    #~~~~~~~~~~~~~~~~

    @property
    def mass_growth_rate(self):
        ''' Mass growth rate (kg_DM/ha/day). '''

        c = self.parameters['conversion_efficiency']['value']

        return c * self.assim_growth

    @property
    def mass_loss_rate(self):
        ''' Loss of root mass (kg_DM/ha/day). '''

        mass = self.mass

        a = self.parameters['loss_param']['value']

        daily_rate = a * mass

        return daily_rate

    #~~~~~~~~~~~~~~~~~~

    @property
    def mass_per_palm(self):
        ''' Mass per palm (kg_DM/palm). '''
        return (1 / self._planting_density) * self.mass

    #~~~~~~~~~~~~~~~~~~

    @property
    def assim_growth(self):
        ''' Assimilates for growth (kg_CH2O/ha/day). '''

        if self._palm is None:
            return self._assim_growth_
        else:
            return self._palm.assimilates.assim_growth_roots

    @property
    def potential_sink_strength(self):
        ''' Potential sink strength (kg_CH2O/ha/day). '''

        c = self.parameters['conversion_efficiency']['value']

        return self.potential_growth_rate / c

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
        potential_turnover = self.mass_loss_rate
        planting_density = self._planting_density

        # 'yearly' -> daily
        c = (1 / self._palm._days_in_year)

        potential_growth = c * planting_density * yearly_per_palm

        return potential_growth + potential_turnover

    @property
    def maintenance_requirement(self):
        ''' Maintenance requirement (kg_CH2O/ha/day). '''

        c = self.parameters['specific_maintenance']['value']

        return c * self.mass
