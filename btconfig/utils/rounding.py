from __future__ import division, absolute_import, print_function


def get_pip_location(value, to_one=True):
    '''
    Returns the pip location for given value

    Ex.
    value=0 - pip location=0
    value=1 - pip location=0
    value=5 - pip location=1 (to_one = True)
    value=5 - pip location=0 (to_one = False)
    value=10 - pip location=1
    value=25 - pip location=2 (to_one = True)
    value=25 - pip location=1 (to_one = False)
    value=0.5 - pip location=0 (to_one = True)
    value=0.5 - pip location=-1 (to_one = False)
    value=0.25 - pip location=0 (to_one = True)
    value=0.25 - pip location=-1 (to_one = False)
    value=0.1 - pip location=-1
    value=0.05 - pip location=-1 (to_one = True)
    value=0.05 - pip location=-2 (to_one = False)
    value=0.01 - pip location=-2
    value=0.001 - pip location=-3
    '''
    pip_location = 0
    if value == 0:
        return pip_location
    while True:
        mult = float(10 ** -pip_location)
        pips = value * mult
        if value >= 1:
            if pips <= 1:
                if pips < 1 and not to_one:
                    pip_location -= 1
                break
            pip_location += 1
        else:
            if pips > 1:
                if to_one:
                    pip_location += 1
                break
            elif pips == 1:
                break
            pip_location -= 1
    return pip_location


def get_pips_from_value(value, pip_location, pip_precision):
    ''' Returns pips from a value '''
    div = float(10 ** pip_location)
    pips = value / div
    return round(pips, pip_precision)


def get_value_from_pips(pips, pip_location, precision):
    ''' Returns price diff from pips '''
    mult = float(10 ** pip_location)
    return get_price_value(pips * mult, precision)


def get_price_value(price, precision):
    ''' Returns a rounded price value '''
    return round(price, precision)


def get_round_to_pip(value, pip_location, precision, round_up=True,
                     round_to_pip=0.5, ensure_dist=False):
    '''
    Rounding to pip

    rounds the given value to the next or previous round_to_pip
    value. It will only round to a precision of 1 (0.1 - 1.0).

        examples round_up=True, round_to_pip=0.5
        1.12585 ==> 1.12590
        1.12897 ==> 1.12900
        1.12555 ==> 1.12560
        1.12864 ==> 1.12865

        examples round_up=False, round_to_pip=0.5
        1.12555 ==> 1.12550
        1.12864 ==> 1.12860
        1.12585 ==> 1.12580
        1.12897 ==> 1.12895
    '''
    # get pips from current value with a precision of 1
    pip = get_pips_from_value(value, pip_location, 1)
    # round pips to the nearest round_to_pip value
    factor = 1 / round_to_pip
    npip = round(pip * factor) / factor

    # ensure pips are above if round_up=True or below if round_up=False
    # given value
    if round_up and npip <= pip:
        npip += round_to_pip
    elif not round_up and npip >= pip:
        npip -= round_to_pip

    if ensure_dist:
        # ensure pip distance is at least given round_to_pip value
        if round_up and npip - pip < round_to_pip:
            npip += round_to_pip
        elif not round_up and pip - npip < round_to_pip:
            npip -= round_to_pip

    res = get_value_from_pips(npip, pip_location, precision)
    return res
