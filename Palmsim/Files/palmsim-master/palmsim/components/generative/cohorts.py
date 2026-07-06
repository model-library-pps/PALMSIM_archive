#!/usr/bin/env python
''' Cohort growth '''

from ..helpers import add_dumps

from .bunch_components import Stalk, MesocarpOil, MesocarpFibers, Kernels

import yaml

from math import exp


@add_dumps
class Cohort(object):
    """ The general model for inflorescence cohorts.

    A cohort is represented by a "mean" inflorescence,
    and a num_inflorescences denoting the number of
    inflorescences in the cohort.

    Concrete sub-classes: Indeterminate, Male, Female.

    Key Properties:
        age : months after initiation
        t_differentiation : -
        mass : mass of the mean inflorescence
        num_inflorescences : number of inflorescences in cohort

    """

    units = yaml.load("""

        abortion_fraction               : '1'
        age                             : 'day'
        assim_growth_cohort             : 'kg_CH2O/cohort/day'
        assim_growth_organ              : 'kg_CH2O/organ/day'
        bunch_failure_dt                : 'days'
        bunch_failure_fraction          : '1/day'
        bunch_failure_t0                : 'days'
        bunch_failure_t1                : 'days'
        cohort_sink_strength            : 'kg_CH2O/cohort/day'
        female_fraction                 : '1'
        has_flowered                    : 'bool'
        inflorescence_abortion_dt       : 'days'
        inflorescence_abortion_fraction : '1/day'
        inflorescence_abortion_t0       : 'days'
        inflorescence_abortion_t1       : 'days'
        is_deletable                    : 'bool'
        is_harvestible                  : 'bool'
        maintenance_requirement         : 'kg_CH2O/organ/day'
        mass                            : 'kg_DM'
        mass_growth_rate                : 'kg_DM/day'
        mass_growth_rate_potential      : 'kg_DM/day'
        mesocarp_oil_content            : '1'
        num_inflorescences              : '1/cohort'
        potential_mass                  : 'kg_DM'
        potential_sink_strength         : 'kg_CH2O/organ/day'
        relative_sink_strength          : '1'
        should_trigger_flowering        : 'bool'
        t_anthesis                      : 'days'
        t_maturity                      : 'days'

    """,
                      Loader=yaml.SafeLoader)

    _prefix = 'cohort'

    @property
    def _MAP(self):
        """ The palm age in months after planting (month). """
        if self._container is None:
            return 0
        else:
            if self._container._palm is None:
                return 0
            else:
                return self._container._palm.MAP

    @property
    def _DAP(self):
        """ The palm age in days after planting (day). """
        if self._container is None:
            return 0
        else:
            if self._container._palm is None:
                return 0
            else:
                return self._container._palm.DAP

#~~~~~~~~~~~~~~~~

    @property
    def potential_sink_strength(self):
        """ The potential sink strength (kg_CH2O/inflorescence/day). """
        return sum([x.potential_sink_strength for x in self.components])

    @property
    def cohort_sink_strength(self):
        """ The potential sink strength of a whole cohort (kg_CH20/cohort/day)"""
        cohort_sink_strength = self.num_inflorescences * self.potential_sink_strength

        return cohort_sink_strength

    def get_relative_sink_strength(self):
        """ Sink strength relative to other organs (1), a partitioning fraction. """

        if self._container is None:
            # assume it is the only one - only used in testing
            return 1

        else:
            total_sink_strength = self._container.potential_sink_strength

            if total_sink_strength == 0:
                return 0
            else:

                # relative sink strength of each cohort
                res = self.cohort_sink_strength / total_sink_strength

                return res

    @property
    def assim_growth_cohort(self):
        """ Assimilates for growth (kg_CH20/cohort organs/month). """

        if self._container is None:
            # only used in testing
            return self.cohort_sink_strength

        else:
            assim_growth_generative = self._container.assim_growth

            return self.relative_sink_strength * assim_growth_generative

    @property
    def assim_growth_organ(self):
        """ Assimilates for growth (kg_CH20/organ/month). """

        if self.num_inflorescences > 0:

            return self.assim_growth_cohort / self.num_inflorescences
        else:
            return 0

#~~~~~~~~~~~~~~~~

    @property
    def mass(self):
        """ The mass (kg_DM). """
        return sum([x.mass for x in self.components])

    @property
    def mass_growth_rate(self):
        """ The mass growth rate (kg_DM/day). """
        return sum([x.mass_growth_rate for x in self.components])

    @property
    def mass_growth_rate_potential(self):
        """ The mass growth rate (kg_DM/day). """
        return sum([x.mass_growth_rate_potential for x in self.components])

#~~~~~~~~~~~~~~~~

    @property
    def maintenance_requirement(self):
        """ The maintenance requirement (kg_CH2O/day). """
        return sum([x.maintenance_requirement for x in self.components])

#~~~~~~~~~~~~~~~~

    def update(self, dt=1):
        """ Update the cohort by dt days. """
        self._update(dt=dt)

    def set_relative_sink_strength(self):
        """ Set the relative sink strength. """
        res = self.get_relative_sink_strength()
        self.relative_sink_strength = res

    def _update(self, dt=1):
        """ Update the cohort by dt days.

        Note
        ----
        We assume abortion fraction is "small"
        s.t. we can use 1-N*epsilon ~= (1-epsilon)**N.
        E.g. 1.01**10 = 1.105 ~= 1 + 10*0.01
        """

        # 1. update the representative bunch components

        # in updating the mass
        # the bunch components will ask
        # the cohort how much assimilates are available
        # for growth given their current age
        for component in self.components:
            component.update_mass(dt=dt)

        # only after the mass growth has been applied
        # we increment the age - namely
        # the sink strength is a function of age
        for component in self.components:
            component.update_age(dt=dt)

        # 2. apply the abortion fractions
        survival_fraction = max(0, (1 - self.abortion_fraction * dt))
        self.num_inflorescences *= survival_fraction

        # 3. increment age
        self.age += dt

#~~~~~~~~~~~~~~~~

    def to_comprehensive_dict(self):
        """ Returns a dict containing comprehensive info. """
        d = self.to_dict()
        for component in self.components:
            d.update(component.to_dict(prefixed=True))
        return d

    @property
    def abortion_fraction(self):
        """ The abortion fraction (1/month). """
        return self._abortion_fraction


#~~~~~~~~~~~~~~~~


class Indeterminate(Cohort):
    """ Models a cohort of indeterminate inflorescences. """

    parameters = yaml.load("""

        abortion_fraction:
            value: 0
            unit: '1/day'
            info: 'Monthly aborted fraction before (!) sex differentiation.'
            source: 'Estimated to be insignificantly small - note, not mentioned in Adam et al. 2011.'

        potential_mass_a:
            value: 31
            unit: 'kg_FM'
            info: 'Co-determines the potential bunch mass.'
            source: 'Calibration via boundary line analysis.'
        
        potential_mass_b:
            value: .10
            unit: '1/year'
            info: 'Co-determines the potential bunch mass.'
            source: 'Calibration via boundary line analysis.'

        t_differentiation:
            value: 0.2
            unit: '1'
            info: 'The time of sex differentiation relative to
                    the duration of the total female phenological cycle.'
            source: 'Calibration - initially based on Adam et al., see fig 3.'

        bunch_FM_to_DM_ratio:
            value: 1.9
            unit: '1'
            info: 'The fresh to dry mass of a bunch.'
            source: 'Afshin, K., Johari, E., Haniff, H., Desa, A., & Farah, S. (2012).
                     The reflection of moisture content on palm oil development during
                     the ripening process of fresh fruits. Journal of Food, Agriculture
                     & Environment, 10(1 part 1), 203-209.'

        """,
                           Loader=yaml.SafeLoader)

    _prefix = 'indeterminate'
    sex = 'indeterminate'

    def __init__(self, container=None):

        # the container keeps track of the cohorts
        self._container = container

        # state
        self.num_inflorescences = 1

        # for prototyping only
        self.t_maturity_ = 1200
        self._female_fraction = 0.9
        self._days_in_year = 365

        # components - here only a stalk
        self.stalk = Stalk(self)

        # in days after frond initiation
        self.age = 0

        # rate
        self.relative_sink_strength = 0

        # param
        self._abortion_fraction = self.parameters['abortion_fraction']['value']
        self.t_differentiation = self._t_maturity * self.parameters[
            't_differentiation']['value']

    @property
    def _t_maturity(self):
        """ Duration of the female phenological cycle from inititation to harvest (days) . """

        parent = self._container

        if parent is None:
            return self.t_maturity_
        else:
            return parent.t_maturity

    @property
    def days_in_year(self):
        if self._container is None:
            return self._days_in_year
        else:
            return self._container._palm._days_in_year

    @property
    def bunch_FM_to_DM_ratio(self):
        if self._container is None:
            return self.parameters['bunch_FM_to_DM_ratio']['value']
        else:
            return self._container.parameters['bunch_FM_to_DM_ratio']['value']

    @property
    def should_differentiate(self):
        """ Should the indeterminate differentiate? (bool). """
        return self.age >= self.t_differentiation

    @property
    def potential_mass(self):
        """ The potential mass (kg_DM). """

        a = self.parameters['potential_mass_a']['value']
        b = self.parameters['potential_mass_b']['value']

        # Potential weight is measured after initiation of the inflorescence.
        x = (self._DAP + self._t_maturity - self._t_maturity *
             self.parameters['t_differentiation']['value']) / self.days_in_year

        res_FM = a * (1 - exp(-b * x))

        # convert FM to DM
        res_DM = res_FM / self.bunch_FM_to_DM_ratio

        assert res_DM >= 0

        return res_DM

    @property
    def components(self):
        """ The sub-organs. """
        return [self.stalk]

    @property
    def female_fraction(self):
        """ Fraction female at sex determination (1). """

        if self._container is None:
            return self._female_fraction

        else:
            return self._container.female_fraction

    def to_male(self):
        """ Returns the associated male inflorescence cohort after sex determination.

        Conceptually converts the indeterminate to a male inflorescence.
        """

        cohort = Male(self._container,
                      potential_mass=self.potential_mass,
                      t_maturity=self._t_maturity)

        cohort.stalk = self.stalk.copy()
        cohort.stalk._cohort = cohort
        cohort.components = [cohort.stalk]
        cohort.age = self.age

        # fractionality
        f = 1 - self.female_fraction

        # Pass on cohort num_inflorescences /relative sink strength
        cohort.num_inflorescences = f * self.num_inflorescences
        cohort.relative_sink_strength = f * self.relative_sink_strength

        return cohort

    def to_female(self):
        """ Returns the associated female inflorescence cohort after sex determination.

        Conceptually converts the indeterminate to a female inflorescence.
        """

        cohort = Female(self._container,
                        potential_mass=self.potential_mass,
                        t_maturity=self._t_maturity)

        # Pass on cohort mean organ state/components
        cohort.stalk = self.stalk.copy()
        cohort.stalk._cohort = cohort
        cohort.components = [cohort.stalk]
        cohort.age = self.age

        # fractionality
        f = self.female_fraction

        # Pass on cohort num_inflorescences /relative sink strength
        cohort.num_inflorescences = f * self.num_inflorescences
        cohort.relative_sink_strength = f * self.relative_sink_strength

        return cohort

    @property
    def is_deletable(self):
        """ When to delete this cohort? (bool)

        Any indeterminate cohort should be deleted
        after sex determination - continues its life
        as a male and female cohort.
        """
        return self.age > self.t_differentiation


class Female(Cohort):

    _prefix = 'female'

    parameters = yaml.load("""

        inflorescence_abortion_t0:
            value: .75
            unit: '1'
            info: 'The point in the phenological cycle at which inflorescence abortion starts.'
            source: 'Calibration - initially based on Adam et al. 2011, see fig 3.'

        inflorescence_abortion_dt:
            value: 0.03
            unit: '1'
            info: 'The fraction of the phenological cycle in which inflorescence abortion occurs.'
            source: 'Calibration - initially based on Adam et al. 2011, see fig 3.'

        bunch_failure_t0:
            value: .92
            unit: '1'
            info: 'The point in the phenological cycle at which bunch failure starts.'
            source: 'Calibration - initially based on Adam et al. 2011, see fig 3.'

        bunch_failure_dt:
            value: 0.03
            unit: '1'
            info: 'The fraction of the phenological cycle in which inflorescence abortion occurs.'
            source: 'Calibration - initially based on Adam et al. 2011, see fig 3.'

        t_anthesis:
            value: 0.82
            unit: '1'
            info: 'The point in the phenological cycle at which anthesis takes place.'
            source: 'Calibration - initially based on Adam et al. 2011, see fig 3.'

        stress_bunch_failure_asymptote:
            value: 0.95
            unit: '1/day'
            info: 'The maximum bunch failure due to stress.'
            source: 'Calibration; based on L.D. Sparnaaijs thesis: The analysis of bunch production. p 26. figure 5.'
            uncertainty: 10%

        stress_bunch_failure_increase:
            value: 10
            unit: '1'
            info: 'The increase in bunch failure per unit increase of the stress index.'
            source: 'Calibration.'
            uncertainty: 10%

        stress_bunch_failure_x0:
            value: 5
            unit: '1'
            info: 'The stress index at which the stress response (slope) is maximum. '
            source: 'Calibration.'

        stress_inflorescence_abortion:
            value: 1

        stress_bunch_failure:
            value: 1

        stress_inflorescence_abortion_asymptote:
            value: 0.95
            unit: '1/day'
            info: 'The maximum infloresence abortion due to stress.'
            source: 'Calibration; based on L.D. Sparnaaijs thesis: The analysis of bunch production. p 26. figure 5.'

        stress_inflorescence_abortion_increase:
            value: 10
            unit: '1/day'
            info: 'The increase in infloresence abortion per unit increase of the stress index.'
            source: 'Calibration.'

        stress_inflorescence_abortion_x0:
            value: 5
            unit: '1'
            info: 'The stress index at which the stress response (slope) is maximum. '
            source: 'Calibration.'
            """,
                           Loader=yaml.SafeLoader)

    _prefix = 'female'
    sex = 'female'

    def __init__(self, container=None, potential_mass=0, t_maturity=1200):

        self._container = container

        # state
        self.num_inflorescences = 1
        self.potential_mass = potential_mass

        self.stalk = Stalk(self)
        self.components = [self.stalk]

        # in days after frond initiation
        self.age = 0

        self.has_flowered = False
        self.t_maturity = t_maturity

        # rate
        self.relative_sink_strength = 0

        # parametrization
        self.set_event_timings()

        # proto-typical value
        self._stress_index_ = 1

    def set_event_timings(self):

        T = self.t_maturity

        self.t_anthesis = T * self.parameters['t_anthesis']['value']

        self.inflorescence_abortion_t0 = T * self.parameters[
            'inflorescence_abortion_t0']['value']
        self.inflorescence_abortion_dt = T * self.parameters[
            'inflorescence_abortion_dt']['value']
        self.inflorescence_abortion_t1 = self.inflorescence_abortion_t0 + self.inflorescence_abortion_dt

        self.bunch_failure_t0 = T * self.parameters['bunch_failure_t0']['value']
        self.bunch_failure_dt = T * self.parameters['bunch_failure_dt']['value']
        self.bunch_failure_t1 = self.bunch_failure_t0 + self.bunch_failure_dt


#~~~~~~~~~~~~~~~~

    def update(self, dt=1):
        """ Update the cohort by dt days. """

        self._update(dt=dt)

        if self.should_trigger_flowering:
            self.set_fruit()

    @property
    def _stress_index(self):
        """ An indicator of plant stress (1) with a range [0,1] - low to high stress. """

        parent = self._container

        if parent is None:
            return self._stress_index_
        else:
            return parent.stress_index

    @property
    def abortion_fraction(self):
        """ The monthly abortion fraction (1/month). """
        return self.inflorescence_abortion_fraction + self.bunch_failure_fraction

    @property
    def inflorescence_abortion_fraction(self):
        """ The inflorescence abortion fraction (1/day). """

        b = self.parameters['stress_inflorescence_abortion']['value']
        if b != 1:
            return 0

        t = self.age

        t0 = self.inflorescence_abortion_t0
        t1 = self.inflorescence_abortion_t1

        if (t >= t0) and (t < t1):
            return self._inflorescence_abortion_fraction
        else:
            return 0

    @property
    def _inflorescence_abortion_fraction(self):
        """ The inflorescence abortion fraction (1/day). """

        x = self._stress_index

        a = self.parameters['stress_inflorescence_abortion_asymptote']['value']
        s = self.parameters['stress_inflorescence_abortion_increase']['value']
        x0 = self.parameters['stress_inflorescence_abortion_x0']['value']

        res = 1 - (1 / exp(a * x))
        #res = 1-((1-a)/(1+exp(s*x-x0))+a) -(1-((1-a)/(1+exp(s*0-x0))+a))

        assert res >= 0
        assert res < 1

        return res

    @property
    def bunch_failure_fraction(self):
        """ The bunch failure fraction (1/day). """

        b = self.parameters['stress_bunch_failure']['value']
        if b != 1:
            return 0

        t = self.age

        t0 = self.bunch_failure_t0
        t1 = self.bunch_failure_t1

        if (t >= t0) and (t < t1):
            return self._bunch_failure_fraction
        else:
            return 0

    @property
    def _bunch_failure_fraction(self):
        """ The bunch failure fraction (1/day). """

        x = self._stress_index

        a = self.parameters['stress_bunch_failure_asymptote']['value']
        s = self.parameters['stress_bunch_failure_increase']['value']
        x0 = self.parameters['stress_bunch_failure_x0']['value']

        res = 1 - (exp(-a * x))
        #res = 1-((1-a)/(1+exp(s*x-x0))+a) -(1-((1-a)/(1+exp(s*0-x0))+a))

        assert res >= 0
        assert res < 1

        return res

    def set_fruit(self):
        """ Initializes additional bunch components:

        - mesocarp oil AND fibers
        - kernel oil
        
        Afterwards

        >>> cohort.has_flowered
        True
        
        """

        self.mesocarp_oil = MesocarpOil(self,
                                        age=self.age,
                                        t_maturity=self.t_maturity)

        self.mesocarp_fibers = MesocarpFibers(self,
                                              age=self.age,
                                              t_maturity=self.t_maturity)

        self.kernel = Kernels(self, age=self.age, t_maturity=self.t_maturity)

        self.components = [
            self.stalk, self.mesocarp_fibers, self.mesocarp_oil, self.kernel
        ]

        self.has_flowered = True

    @property
    def should_trigger_flowering(self):
        """ A boolean indicating whether "set_fruit" should be triggered. """
        return self.age > self.t_anthesis and not self.has_flowered

    @property
    def is_harvestible(self):
        """ Indicates whether this cohort is harvestible. """
        return self.age >= self.t_maturity

    @property
    def is_deletable(self):
        """ When to delete this cohort? (bool) - (metabolically inactive) """
        return self.age >= self.t_maturity


class Male(Cohort):
    _prefix = 'male'
    _version = '0.0'

    parameters = yaml.load("""

        t_anthesis:
            value: 0.82
            unit: '1'
            info: 'The point in the phenological cycle at which anthesis takes place.'
            source: 'Adam et al. 2011, see fig 3.'

            """,
                           Loader=yaml.SafeLoader)

    _prefix = 'male'
    sex = 'male'

    def __init__(self, container=None, potential_mass=0, t_maturity=1200):

        self._container = container

        # state

        # in practice the initial values will be set
        # upon sex determination via the associated indeterminate cohort
        # see "Indeterminate.to_male"

        self.potential_mass = potential_mass
        self.num_inflorescences = 1

        # components
        self.stalk = Stalk(self)
        self.components = [self.stalk]

        # in days after frond initiation
        self.age = 0
        self.has_flowered = False

        # of the female counter-part - used as a reference
        self.t_maturity = t_maturity

        self.relative_sink_strength = 0

        # we do not model abortion of male inflorescences
        # and thus keep it at a value of zero.
        self._abortion_fraction = 0

    @property
    def is_deletable(self):
        """ When to delete this cohort? (bool) - (metabolically inactive) """
        return self.age > self.t_maturity