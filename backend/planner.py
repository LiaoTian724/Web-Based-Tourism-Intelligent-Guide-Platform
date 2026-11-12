from math import asin, cos, radians, sin, sqrt


def walk_minutes(origin, destination):
    # Estimate walking time between two attractions.
    if origin is None:
        return 0
    
    # Convert latitude and longitude to radians.
    lat1 = radians(origin.latitude)
    lon1 = radians(origin.longitude)
    lat2 = radians(destination.latitude)
    lon2 = radians(destination.longitude)

    # Haversine formula.
    arc = (sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2)
    distance_km = 6371 * 2 * asin(sqrt(min(1, arc)))

    # Estimated road detour: 1.3
    # Walking speed: 4 km/h
    return max(1, round(distance_km * 1.3 / 4 * 60))


def build_plan(attractions, interests, budget_minutes):
    # Build an itinerary with at most four attractions.

    remaining = list(attractions)
    stops = []
    used_minutes = 0
    origin = None

    while remaining and len(stops) < 4:
        candidates = []

        for place in remaining:
            walk = walk_minutes(origin, place)
            cost = walk + place.visit_minutes

            if used_minutes + cost <= budget_minutes:
                candidates.append((place.category not in interests, cost, place.pk, walk, place,))

        if not candidates:
            break

        _, cost, _, walk, chosen = min(candidates)

        stops.append(
            {
                "attraction": chosen,
                "walk_minutes": walk,
                "visit_minutes": chosen.visit_minutes,
            }
        )

        used_minutes += cost
        remaining.remove(chosen)
        origin = chosen

    return stops, used_minutes
