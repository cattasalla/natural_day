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

def get_sunrise(oneday_data):
    return get_phen_datetime(oneday_data, 'sun', 'Rise')

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


