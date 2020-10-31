from math import cos, asin, sqrt

def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p)*cos(lat2*p) * (1-cos((lon2-lon1)*p)) / 2
    return 12742 * asin(sqrt(a))

def closest(other_users, my_user):
    return min(other_users, key=lambda p: distance(my_user.lat, my_user.long, p.lat, p.long))

# tempDataList = [{'lat': 39.7612992, 'long': -86.1519681},
#                 {'lat': 39.762241,  'long': -86.158436 },
#                 {'lat': 39.7622292, 'long': -86.1578917}]
#
# v = {'lat': 39.7622290, 'lon': -86.1519750}
# print(closest(tempDataList, v))