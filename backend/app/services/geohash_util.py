BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"


def encode(latitude: float, longitude: float, precision: int = 4) -> str:
    lat_min, lat_max = -90.0, 90.0
    lng_min, lng_max = -180.0, 180.0
    bits = [16, 8, 4, 2, 1]
    geohash: list[str] = []
    bit = 0
    ch = 0
    even = True

    while len(geohash) < precision:
        if even:
            mid = (lng_min + lng_max) / 2
            if longitude >= mid:
                ch |= bits[bit]
                lng_min = mid
            else:
                lng_max = mid
        else:
            mid = (lat_min + lat_max) / 2
            if latitude >= mid:
                ch |= bits[bit]
                lat_min = mid
            else:
                lat_max = mid
        even = not even
        if bit < 4:
            bit += 1
        else:
            geohash.append(BASE32[ch])
            bit = 0
            ch = 0
    return "".join(geohash)
