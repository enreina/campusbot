from geopy.distance import geodesic

foodBeveragePlaces = [
    {
        "name": "VMBW6 / EEMCS - F&B Corner",
        "latitude": 51.9993422,
        "longitude": 4.3776795
    },
    {
        "name": "Civil Engineering and Geosciences - F&B corner",
        "latitude": 51.9991589,
        "longitude": 4.3749481
    },
    {
        "name": "Cafe X",
        "latitude": 51.9991588,
        "longitude": 4.3710613
    }
]
def findNearestPlaceItem(latitude, longitude):
    distances = []
    for place in foodBeveragePlaces:
        distances.append(
            {
                "name": place["name"],
                "distance": geodesic((place['latitude'],place['longitude']), (latitude, longitude)).meters
            }
        )

    sortedDistances = sorted(distances, key = lambda i: i['distance'])

    return [{"name":x["name"]} for x in sortedDistances[:2]]

