from typing import Dict, Optional


def get_workout_params(
    include_ride_details: bool, include_instructor_details: bool
) -> Optional[Dict[str, str]]:
    if include_ride_details or include_instructor_details:
        joins = []
        if include_ride_details:
            joins.append("ride")
        if include_instructor_details:
            joins.append("ride.instructor")
        return {"joins": ",".join(joins)}

    return None
