import requests

#import termcolor

from datetime import datetime as dt
from datetime import timedelta

import pandas as pd
import numpy as np

import argparse


def set_api():
    return "https://aa.usno.navy.mil/api", "astro_year_script"

def set_lat_lon(parser):
    parser.add_argument(
        '--lat', help = "latitude",
        default = 
        '39.79'
    )
    parser.add_argument(
        '--lon', help = 'longitude',
        default = '-86.14'
    )
    return parser

def set_time_zone(parser):
    parser.add_argument(
        'tz', help = 'time zone',
        default = -5
    )

def set_time(parser):
    parser.add_argument('--time',
                        help = 'string in form of %Y%m%d-%H%M')
    parser.add_argument('--dst',
                        default = "true")

def set_date(parser):
    parser.add_argument('--date',
                        help = 'string in form of %Y%m%d')

def set_writeout(parser):
    parser.add_argument('--write',
                        help = 'write out bao or nayi'
                        )

def get_lat_lon(args):
    return args.lat, args.lon

def get_now_time(args):
    if args.time:
        return dt.strptime(args.time, "%Y%m%d-%H%M")
    elif args.date:
        return dt.strptime(args.date, "%Y%m%d")
    else:
        return dt.now()

def get_yesterday(now):
    return now - timedelta(days = 1)

def get_timezone(args):
    return args.tz

def get_params(args):
    return {
        'date':dt.strftime(get_now_time(args), "%Y-%m-%d"),
        'coords':f"{args.lat, args.lon}",
        'tz':args.tz,
        'dst':args.dst
    }

def get_oneday_data(BASE, params):
    url = f"{BASE}/rstt/oneday"
    return requests.get(
        url = url,
        params = params
    ).json()['properties']['data']

def get_nxtday_data(BASE, params, now):
    params_local = params
    params_local['date'] = dt.strftime(now + timedelta(days=1), '%Y-%m-%d')
    return get_oneday_data(BASE, params_local)
    

def get_phen_time(data, phen, phenfield='phen'):
    return [item for item in data if item[phenfield] == phen][0]['time']

def make_str_for_phen_datetime(oneday_data:dict,body:str = 'sun',phen:str='Rise', phenfield = 'phen'):
    year = oneday_data['year']
    month = oneday_data['month']
    day = oneday_data['day']
    bodydata = oneday_data[f"{body}data"]
    phen_time = get_phen_time(bodydata, phen)
    phen_hour = phen_time.split(" ")[0]
    phen_minute = phen_time.split(" ")[2]
    datestr = f"{year}-{month:02d}-{day:02d}"
    timestr = f"{phen_hour} E{phen_minute}"
    return f"{datestr} {timestr}"

def get_phen_datetime(oneday_data:dict, body:str = 'sun', phen:str='Rise', phenfield = 'phen'):
    str4_datetime = make_str_for_phen_datetime(oneday_data, body, phen, phenfield)
    return dt.strptime(str4_datetime,datetime_format)

#def get_sunrise(oneday_data):
#    return get_phen_datetime(oneday_data, 'sun', 'Rise')

def get_sunrises_sunset(oneday_data, nxtday_data):
    return (get_phen_datetime(oneday_data, 'sun', 'Rise'),
        get_phen_datetime(oneday_data, 'sun', 'Set'),
            get_phen_datetime(nxtday_data, 'sun', 'Rise'))

def get_daylength(sunpoint1, sunpoint2):
    return sunpoint2 - sunpoint1

def get_unitlength_from_daylength(day_length, n_segments):
    return  day_length/n_segments

def get_unitlength(sunpoint1, sunpoint2, n_segments):
    return get_daylength(sunpoint1, sunpoint2)/n_segments

def get_unittimes(sunpoint1, unitlength, n_segments):
    return [sunpoint1 + unitlength*t for t in range(n_segments+1)]

def make_time_df(unit_name, n, day_times, night_times):
    return pd.DataFrame({
        unit_name: list(range(n+1)),
        'time': list(day_times)[:-1] + list(night_times)
    })

##### currently around line 80

def main():

    BASE, APP_ID = set_api()

    parser = argparse.ArgumentParser()
    set_lat_lon(parser)
    set_time_zone(parser)
    set_time(parser)
    set_date(parser)
    set_writeout(parser)
    args = parser.parse_args()

    params = get_params(args)
    oneday_data = get_oneday_data(BASE, params)
    nxtday_data = get_nxtday_data(BASE, params)

    sunrise, sun_set, nxtrise = get_sunrises_sunset(oneday_data, nxtday_data)

    day_length = get_daylength(sunrise, sun_set)
    bao_day_length = get_unitlength(sunrise, sun_set, 4)
    nayi_day_length = get_unitlength(sunrise, sun_set, 30)
    nayipati_day_length = get_unitlength(sunrise, sun_set, 30*4)

    bao_day_times = get_unittimes(sunrise, bao_day_length, 4)
    nayi_day_times = get_unittimes(sunrise, nayi_day_length, 30)
    nayipati_day_times = get_unittimes(sunrise, nayi_day_length, 30*4)

    night_length = get_daylength(sun_set, nxtrise)
    bao_night_length = get_unitlength(sun_set, nxtrise, 4)
    nayi_night_length = get_unitlength(sun_set, nxtrise, 30)
    nayipati_night_length = get_unitlength(sun_set, nxtrise, 30*4)

    bao_night_times = get_unittimes(sun_set, bao_night_length, 4)
    nayi_night_times = get_unittimes(sun_set, nayi_night_length, 30)
    nayipati_night_times = get_unittimes(sun_set, nayipati_night_length, 30*4)

    bao = make_time_df('bao', 4, bao_day_times, bao_night_times)
    nayi = make_time_df('nayi', 30, nayi_day_times, nayi_night_times)
    #nayipati = make_time_df(nayi)

    
