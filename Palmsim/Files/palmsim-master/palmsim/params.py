import sys
import os
import yaml

from .components.fronds import Fronds
from .components.trunk import Trunk
from .components.roots import Roots
# from .components.generative import Organs
from .components.assimilates import Assimilates
from .components.management import Management
from .components.soil import Soil
from .components.weather import Weather
from .components.generative import Indeterminate, Male, Female
from .components.generative import Stalk, MesocarpFibers, MesocarpOil, Kernels

MODULE_FILEPATH = sys.modules[__name__].__file__
MODULE_DIR = os.path.dirname(MODULE_FILEPATH)

CLASSES = [
    Fronds, Trunk, Roots, Assimilates, Soil, Weather, Indeterminate, Male,
    Female, Stalk, MesocarpFibers, MesocarpOil
]


def get_parameters_config():
    ''' Get the default parameters of the model. '''
    config_dict = {}

    for kls in CLASSES:
        config_dict[kls._prefix] = kls.parameters

    preamble = 'INFO\n\n'

    preamble += 'Number of parameters per sub-model'
    preamble += '\n------------------------------'

    for kls in config_dict:
        params = config_dict[kls]
        preamble += '\n{:<20} {:}'.format(kls, len(params))

    dump = yaml.dump(config_dict, default_flow_style=False)

    preamble = '\n'.join(['# ' + x for x in preamble.splitlines()])

    config_text = preamble + '\n\n# Parameters per sub-model:\n\n' + dump

    return config_text


def save_parameters_config(filename='settings.yaml'):
    ''' Makes the settings file (settings.yaml) based on the defaults. '''

    config_text = get_parameters()

    filepath = os.path.join(MODULE_DIR, filename)

    with open(filepath, 'w') as f:
        f.write(yaml.dump(config_text, default_flow_style=False))

    return config_text


def get_parameters():
    ''' Gets the parameters of all sub-models.

    Returns
    -------
    A nested-dictionary of parameters per sub-model.
    '''
    config_dict = {}

    for kls in CLASSES:
        config_dict[kls._prefix] = kls.parameters

    return config_dict


def set_parameters_old(settings=None):
    ''' Sets the parameters of all sub-models.

    Input
    -----
    settings: dict
        A nested-dictionary of parameters per sub-model.

    '''
    if settings is None:
        return False
    else:
        print('Setting settings...')
        for kls in CLASSES:

            params = settings[kls._prefix]

            kls.parameters = params


def set_parameters(obj, settings=None):
    ''' Sets the parameters of all sub-models.

    Input
    -----
    settings: dict
        A nested-dictionary of parameters per sub-model.

    '''
    if settings is None:
        return False
    else:
        print('Setting settings...')

        for pars in settings:
            if pars in dir(obj):
                sub_obj = getattr(obj, pars)
                for kls in CLASSES:
                    if isinstance(sub_obj, kls):
                        sub_obj.parameters = settings[pars]


SETTINGS_FILENAME = 'settings.yaml'


def load_parameters(SETTINGS_FILENAME):

    SETTINGS = None

    print('Trying to load settings from file...')

    if SETTINGS_FILENAME in os.listdir(MODULE_DIR):

        filepath = os.path.join(MODULE_DIR, SETTINGS_FILENAME)

        with open(filepath, 'r') as f:
            SETTINGS_TEXT = f.read()
            SETTINGS = yaml.load(SETTINGS_TEXT, Loader=yaml.SafeLoader)

        set_parameters(SETTINGS)


#load_parameters(SETTINGS_FILENAME)