import math

# haversine formula
# https://www.geeksforgeeks.org/haversine-formula-to-find-distance-between-two-points-on-a-sphere/
# by ChitraNayal
def haversine(lat1, lon1, lat2, lon2):
    # distance between latitudes
    # and longitudes
    dLat = (lat2 - lat1) * math.pi / 180.0
    dLon = (lon2 - lon1) * math.pi / 180.0

    # convert to radians
    lat1 = (lat1) * math.pi / 180.0
    lat2 = (lat2) * math.pi / 180.0

    # apply formulae
    a = (pow(math.sin(dLat / 2), 2) +
         pow(math.sin(dLon / 2), 2) *
             math.cos(lat1) * math.cos(lat2) )

    c = 2 * math.asin(math.sqrt(a))
    rad = 6371
    return rad * c

if __name__ == "__main__":
    # Big Ben in London (51.5007° N, 0.1246° W)
    lat1 = 51.5007
    lon1 = 0.1246
    # The Statue of Liberty in New York (40.6892° N, 74.0445° W)
    lat2 = 40.6892
    lon2 = 74.0445
    #  is 5574.8 km.
    print(haversine(lat1, lon1,lat2, lon2), "km")
