#!/usr/bin/python
# -*- coding: <encoding name> -*-
 
from datetime import datetime
import requests
import os

class NightscoutException(Exception): pass

def get_entries(retries=0, last_exception=None):
    if retries >= 3:
        print("Retried too many times: %s" % last_exception)
        raise NightscoutException(last_exception)

    try:
        host = os.environ['NSDASH_URL']
        resp = requests.get(f'{host}/api/v1/entries/sgv.json?count=2', verify=False, timeout=5)
            # For the sake of keeping this portable without adding a lot of complexity, don't verify SSL certificates.
            # https://github.com/kennethreitz/requests/issues/557
            # Don't let bad connectivity cause the app to freeze
    except requests.exceptions.Timeout as e:
        # Don't retry timeouts, since the app is unresponsive while a request is in progress,
        # and a new request will be made in UPDATE_FREQUENCY_SECONDS seconds anyway.
        print("Timed out: %s" % repr(e))
        raise NightscoutException(repr(e))
    except requests.exceptions.RequestException as e:
        return get_entries(retries + 1, repr(e))

    if resp.status_code != 200:
         return get_entries(retries + 1, "Nightscout returned status %s" % resp.status_code)

    try:
        arr = resp.json()
        if type(arr) == list and (len(arr) == 0 or type(arr[0]) == dict):
            return arr
        else:
            return get_entries(retries + 1, "Nightscout returned bad data")
    except simplejson.scanner.JSONDecodeError:
        return get_entries(retries + 1, "Nightscout returned bad JSON")

def maybe_convert_units(mgdl):
    #TODO: make  config/env var
    return round(mgdl / 18.0182, 1) if True else mgdl

def filter_bgs(entries):
    bgs = [e.copy() for e in entries if 'sgv' in e]
    for bg in bgs:
        bg['sgv'] = int(bg['sgv'])
    return bgs

def seconds_ago(timestamp):
    return int(datetime.now().strftime('%s')) - timestamp / 1000

def get_direction(entry):
    return {
        'DoubleUp': u'⇈',
        'SingleUp': u'↑',
        'FortyFiveUp': u'↗',
        'Flat': u'→',
        'FortyFiveDown': u'↘',
        'SingleDown': u'↓',
        'DoubleDown': u'⇊',
    }.get(entry.get('direction'), '-')

def get_delta(last, second_to_last):
    return ('+' if last['sgv'] >= second_to_last['sgv'] else u'−') + str(abs(maybe_convert_units(last['sgv'] - second_to_last['sgv'])))

def get_data():
    entries = get_entries()
    bgs = filter_bgs(entries)
    last, second_to_last = bgs[0:2]
    if (last['date'] - second_to_last['date']) / 1000 <= 1000:
        delta = get_delta(last, second_to_last)
    else:
        delta = '?'
    return {
        "sgv": maybe_convert_units(last['sgv']),
        "direction": get_direction(last),
        "minutes_ago": int(seconds_ago(last['date']) / 60),
        "delta": delta
    }
