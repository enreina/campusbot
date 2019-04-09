from geopy.distance import geodesic
import db.firestoreClient as FirestoreClient

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

def findNearestBuilding(latitude, longitude, limit=3):
    buildingCategory = FirestoreClient.getDocumentRef('categories', 'building')
    buildings = FirestoreClient.getDocuments('placeItems', [('category', '==', buildingCategory)])

    distances = []
    for building in buildings:
        buildingLatitude = building['geolocation']['latitude']
        buildingLongitude = building['geolocation']['longitude']
        distances.append(
            {
                "text": building["name"],
                "value": building["_id"],
                "distance": geodesic((buildingLatitude,buildingLongitude), (latitude, longitude)).meters
            }
        )

    sortedDistances = sorted(distances, key = lambda i: i['distance'])

    return [{"text":x["text"], "value":x["value"]} for x in sortedDistances[:limit]]
    
