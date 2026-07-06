# History

2.5.2 (2019-12-11)
**Bug Fixes**

- Recent changes to the model broke the example applications of the model provided in the repository. The examples
  have been updated to reflect changes to the model and some small modifications have been made to the Indeterminate-
  class to allow stand-alone simulation of a single inflorescence.
- All calls to yaml.load() have been updated to explicitly specify the SafeLoader as the loader to use when reading
  yaml-files.

## 2.5.1 (2019-06-24)

**Improvements**
Cohort

- Bunch stress does now only require one parameter indicating the stress.

**Bug Fixes**
Cohort

- Potential bunch weight is now determined including the t_maturity. Otherwise bunch weight
  is lagging behind.
- Potential bunch weight is correcting by removing the reset of the stalk component.

**Comments**

- Unnecessary code is removed in all components

## 2.5.0 (2019-04-10)

**Improvements**
Trunk

- Active trunk mass is now determined based on trunk density and lignification.

Management

- Pruning is modelled in an easier way, the leafs are kept at an optimal relation. Leafs are not pruned at a specific time period.
- Optimal pruning is based on optimal management practices by Wottiez.
- Evaporation and transpiration are separated by assuming that a fraction of 0.12 is evaporation when an optimal leaf area index is reached.
- The management component was removed from the code. Pruning is now done in the fronds component.
- Time maturity curve is slightly adjusted, to use less parameters.

**Bug Fixes**

**Comments**

- Unnecessary code is remove as a result of the pruning.

  2.4.5a (2019-03-29)

---

**Bug Fixes**
Fronds

- Corrected gaussian values
- Specific maintenance rachis corrected 0.002 -> 0.0018 (Dufrene, 1990)
- Converstion efficiency fronds corrected 0.67 -> 0.73 (Dufrene, 1990)
- Intial frond mass adjusted to 0.1

Roots

- New root loss parameter
- One root loss parameter removed based on Henson
- Mass_loss_rate was multiplied by planting density??? Check once more
- Initial seedling weight roots is adjusted.

Trunk

- Intial seedling weight trunk is adjusted.
- Trunk specific maintenance gecorrigeerd by factor 10 ==0.005 kgCH2O/kg_DM/day.

Weather

- Emperical relation for fraction_diffuse was given for hourly data but was channged to daily data.
- Canopy_net_radiation for a reference crop was added and was coupled to the FAO-56 Penman-Monteith equation
- Small windspeed fix to FAO-56 Penman-Monteith equation
- Add eccentricity formula to extraterrestrial daily
- Edited eccentricity formula, was wrongly formulated. (error tolerance not needed anymore)

**Comments**
Cohorts:

- Removed uneccessary code.

Management:

- Removed unneccesarry code, DEFAULT Plantin density
- comments at fronds count t0 was modified

Constants & helper

- Constant was removed
- Unnecessary code was removed from all codes.
- Bunch component quadratic and linear function were moved to helper code.

Fronds

- Removed abundant code daylength

Trunk

- Removed unneccessary code from component trunk

Soil

- Put parameters in soil component in alphabetical order
- Soil removed initial values, is now assumed that soil has FC soil moisture at planting
- Cleared soil component by removing IRHO and removing unneccessary code

Weather

- Put parameters in weather file in alphabetical order
- Move conversion from degrees to radials to helper functions
- Remove radian function from calc_radiation_extraterrestrial
- Change comment in weather class, edited sources in APA
- Slight change stefan boltzmann constant + add source
- Add eccentricity formula as a separate object
- New formulation of the FAO-56 Penman-Monteith equation

## 2.4.4a (2019-01-10)

**Improvements**

- Potential evapotranspiration now estimated using Penman-Monteith combination equation instead of the IRHO method.
- Revised examples
- Removed redundant files

  2.4.3a (2019-01-10)

---

**Improvements**

- Stress responses modelled using sigmoids instead of linear relationships without an asymptote.

**Bug Fixes**

- Soil updating - earlier didnt appropriately take into account dt.

  2.4.1a (2019-01-10)

---

**Improvements**

- SUCROS style photosynthesis
- Shortage of assimilates for generative growth as THE stress index.

  2.4.0a (2018-12-12)

---

**Improvements**

- Support for daily time-steps of integration
- Improved the calibration of potential - trunk mass - root mass - bunch mass - female fraction

  2.3.4a (2018-11-13)

---

**Improvements**

- HISTORY.md -- the dates might be a bit off (+- 1 month) before March 2018.
- An API spec file API.md

  2.3.3a (2018-10-01)

---

**Improvements**

- added an example jupyter notebook on biomass production
- made sure examples 1--7 are up-to-date and run
- started to actively use versioning

  2.3.2a (2018-10-31)

---

**Improvements**

- refactored the generative sub-module (one file) into a package (multiple files)
- bunch phenology parametrization: start (mo after initiation) and duration of abortion sensitive phases instead of start and stop
- prototype of a calibration tool: knobs and sliders for humans to try and calibrate the model

  2.3.1a (2018-03):

---

**Testing**

- Compared predicted vs observed bunch counts for Ghana (2013--2016)
- Overall quite agreeable however - N = 1 - only bunch counts --- bunch weights were off

**Improvements**

- model decrease of evapotranspiration with water stress (sigmoid of stress)
- model decrease of assimilation with water stress (linear via WUE)
- water-stress modelled via soil moisture content (-) instead of soil water deficit (mm)

  2.3.0a (2018-02):

---

**Improvements**

Water-stress effects:

- Water-stress (proxy: soil water deficit) decreases the - female:male ratio - inflorescence "survival" (abortion phase before anthesis) - bunch "survival" (abortion phase after anthesis)

  2.2.0a (2018-01)

---

**Testing**

- Sensibility test of growth/mass of components: passed for potential production

**Improvements**

- Switch to using relative sink strength to partition assimilates instead of fixed partitioning (trunk catastrophe - kept on growing in v1.0)
- Inflorescences modelled via "bunch components" each having a potential sink strength that changes over time (phenology): - stalks - mesocarp fibers - mesocarp oil - kernels

**Bugfixes**

Fixed on-set of bunch growth:

- in previous versions the growth of the first bunches was very unrealistic due to a combination of fixed assimilate partitioning and little maintenance demand: first bunches would "explode" and their maintenance demand would "crash" the palm - see the glitches in the bunch production in A.C. Vera's report.
- fixed by smoothening the bunch production transition from zero inflorescences to N --- using a logistic function.

  2.1.0a (2017-12)

---

**Improvements**

- Changed the estimate of leaf area from SLA based to YAP based (Gerritsma and Soebagyo, 1998): more accurate.
- Changed the modelling of pruning: via frond count instead of via standing mass.

  2.0.0a (2017-11)

---

- Re-implemented PALMSIM: MatLab -> Python
- Direct port - exactly the same behaviour as 1.0

**Improvements**

- Added basic documentation of parameters and model variables (units, references)

  1.0b (2014)

---

- Presumably minor changes by M. Hoffman
- Paper by M. Hoffman and others: Model description, evaluation and application
- Available online (PPS models portal)

## pre-1.0 (2010)

- Conception by A. C. Vera
- MatLab
- functional programming style --- basically a big script

## pre-0.1 (2009)

Media attention: - bio-fuels - OP - perennials - rainforts
