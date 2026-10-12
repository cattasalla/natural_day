import requests

#import termcolor

from datetime import datetime as dt
from datetime import timedelta

import pandas as pd
import numpy as np

import argparse

# ── USNO API base ────────────────────────────────────────────────────────────
BASE = "https://aa.usno.navy.mil/api"
APP_ID = "astro_year_script"  # optional identifier for USNO

# set location
latitude  = "39.79"
longitude = "-86.14"

# time zone (relative to UTC)
tz = -5

# earlier version used these
#year = 2026
#month = 6
#day = 19

parser = argparse.ArgumentParser()
parser.add_argument("--time", help = "string in form of %Y%m%d-%H%M")
parser.add_argument("--date", help = "string in form of %Y%m%d")
parser.add_argument("--write", help = "print times for day (bao/nayi)")
args = parser.parse_args()
if args.time:
    now = dt.strptime(args.time, "%Y%m%d%H%M")
elif args.date:
    now = dt.strptime(args.date, "%Y%m%d")
else:
    # get now
    now = dt.now()
yesterday = dt.now() - timedelta(days=1)
#print(now)

# namedate = f"{year}-{month:02d}-{day:02d}"
# account for DST
dst = "true"

datetime_format = "%Y-%m-%d %H:%M %Z"

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
##########################
# get today's data (by xian date0
params = {
        'date':dt.strftime(now, "%Y-%m-%d"),
        'coords':f"{latitude},{longitude}",
        'tz':tz,
        'dst':dst,
    }

oneday_data = requests.get(url=f"{BASE}/rstt/oneday",params = params).json()['properties']['data']

# is it before sunrise? if not, the buddhist day starts the previous sunrise
sunrise = get_phen_datetime(oneday_data, 'sun', 'Rise')

if sunrise > now:
    params['date'] = dt.strftime(yesterday, "%Y-%m-%d")
    oneday_data = requests.get(url=f"{BASE}/rstt/oneday",params = params).json()['properties']['data']
    params['date'] = dt.strftime(now, "%Y-%m-%d")
    #nxtday_data = requests.get(url=f"{BASE}/rstt/oneday", params=params).json()['properties']['data']
else:
    params['date'] = dt.strftime(now + timedelta(days=1), "%Y-%m-%d")

nxtday_data = requests.get(url=f"{BASE}/rstt/oneday",params = params).json()['properties']['data']

#print(oneday_data)
# get sunrise and sunset
sunrise = get_phen_datetime(oneday_data, 'sun', 'Rise')
sun_set = get_phen_datetime(oneday_data, 'sun', 'Set')
nxtrise = get_phen_datetime(nxtday_data, 'sun', 'Rise')

# get the tay times. it works better to just compute the units and
# loop to build the set through sums than pd.date_range
day_length = sun_set - sunrise
day_bao_length = 0.25*day_length
day_bizana_length = day_length/(30*60)

# there are four bao between sunrise and sunset
# there are 30 nayi, with 60 bizana in each, between sunrise and sunset
bao_day_times = [sunrise + day_bao_length*bao for bao in range(5)]
bizana_day_times = [sunrise + day_bizana_length*bizana for bizana in range((30*60)+1)]

# as above but for night
night_length = nxtrise - sun_set
night_bao_length = 0.25*night_length
night_bizana_length = night_length/(30*60)

bao_night_times = [sun_set + night_bao_length*bao for bao in range(5)]
bizana_night_times = [sun_set + night_bizana_length*bizana for bizana in range((30*60)+1)]

# construct the list of the times
bao_numbers = [f"bao {x}" for x in range(9)]
nayi_bizana_numbers = [f"{int(np.floor(x/60)):02d}:{x%60:02d}" for x in range(3601)]

# create dataframes for the day
bao_dataframe = pd.DataFrame({'bao':bao_numbers, 'xian':list(bao_day_times)[:-1] + list(bao_night_times)})
nayi_bizana_dataframe = pd.DataFrame({'nayi_bizana':nayi_bizana_numbers,
                                     'xian':list(bizana_day_times)[:-1] + list(bizana_night_times)})
#print(nayi_bizana_dataframe)

bizana_times = list(bizana_day_times)[:-1] + list(bizana_night_times)
bao_times = list(bao_day_times)[:-1] + list(bao_night_times)

#print(pd.DataFrame({"bao":[x for x in range(8)] + [0], "xian":bao_times}))
#print(pd.DataFrame({"nayi":}))
#print(bao_dataframe)
#print(nayi_bizana_dataframe)
if args.write == "bizana" or args.write == "both":
    print(nayi_bizana_dataframe)
    nayi_bizana_dataframe.to_csv(f"{now.strftime("%Y%m%d")}_bizana.csv", index=False)
if args.write == "bao" or args.write == "both":
    bao_dataframe.to_csv(f"{now.strftime("%Y%m%d")}_bao.csv", index=False)
if args.write == "nayi" or args.write == "both":
    nayi_bizana_dataframe.loc[0::60].to_csv(f"{now.strftime("%Y%m%d")}_nayi.csv", index=False)


if not args.date:
    # write out the info of interest
    i = np.argmin(np.abs(now-nayi_bizana_dataframe['xian']))
    j = np.argmin(np.abs(now-bao_dataframe['xian']))
    if now < bao_dataframe.loc[j, 'xian']:
        j -= 1
    print(f"Christian-capitalist time is: \033[7m\033[31m{now}\033[0m")
    print(f"bao:nayi:bizana is: \033[103;30m{bao_dataframe.loc[j, 'bao'][4:]}:{nayi_bizana_dataframe.loc[i, 'nayi_bizana']}\033[0m")
    if now < sun_set:
        print(f"bao length is {day_bao_length}")
        print(f"nayi length is {day_bizana_length*60}")
    else:
        print(f"bao length is {night_bao_length}")
        print(f"nayi length is {night_bizana_length*60}")
else:
    print(bao_dataframe)
    print(nayi_bizana_dataframe.loc[[i for i in range(60) if i%5==0], ])

print(f"Today's lunar coverage is {oneday_data['fracillum']} with the moon in {oneday_data['curphase']}")

# also figure out the date relative to the wheel of the year
year = now.year

seasons_yr1 = requests.get(f"{BASE}/seasons", {"year": year, "ID": APP_ID,'coords':f"{latitude},{longitude}",
    'tz':tz,
    'dst':dst}).json()['data']
seasons_yr2 = requests.get(f"{BASE}/seasons", {"year": year + 1, "ID": APP_ID,'coords':f"{latitude},{longitude}",
    'tz':tz,
    'dst':dst}).json()['data']
seasons_yr1.extend(seasons_yr2)

def get_datetime_from_seasons(x):
    return dt(
        year = x['year'],
        month = x['month'],
                    day = x['day'],
                    hour = int(x['time'][:2]),
                    minute = int(x['time'][3:5])
    )


spring1 = get_datetime_from_seasons(seasons_yr1[1])
summer1 = get_datetime_from_seasons(seasons_yr1[2])
autumn1 = get_datetime_from_seasons(seasons_yr1[4])
winter1 = get_datetime_from_seasons(seasons_yr1[5])
spring2 = get_datetime_from_seasons(seasons_yr1[7])

def get_semiseason_dates(date1, date2):
    return pd.date_range(date1, date2, periods = 3)[1]

beltane = get_semiseason_dates(spring1, summer1)#.strftime("%H:%M"))
lugnasadh = get_semiseason_dates(summer1, autumn1)
samhain = get_semiseason_dates(autumn1, winter1)
imbolc = get_semiseason_dates(winter1, spring2)

wheel_of_year = [spring1, beltane, summer1, lugnasadh, autumn1, samhain, winter1, imbolc, spring2]
wheel_of_year_names = ["OSTARA", "BELTANE", "LITHA", "LUGNASADH", "MABON", "SAMHAIN", "YULE", "IMBOLC", "OSTARA2"]

i = np.argmin([np.abs((t - now).days) for t in wheel_of_year])
if wheel_of_year[i] > now:
    i -= 1
degr = (wheel_of_year[i+1] - wheel_of_year[i])/45
print(f"\033[46;30m{wheel_of_year_names[i]}-{(now - wheel_of_year[i]).days+1}\033[0m")
print(f"{(wheel_of_year[i + 1] - now).days} until {wheel_of_year_names[i+1]} on {wheel_of_year[i+1].date()}")
tryme = 0
while now > wheel_of_year[i]+tryme*degr:
    tryme += 1
print(f"{tryme} degrees of {wheel_of_year_names[i]} (1 degree = {degr})")
