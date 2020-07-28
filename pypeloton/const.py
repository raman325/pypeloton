from .version import __version__

BASE_URL = "https://api.onepeloton.com"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": f"pypeloton v{__version__} (https://github.com/raman325/pypeloton)",
}

BASE_API_URL = f"{BASE_URL}/api"
ENDPOINTS = {
    "LOGIN": f"{BASE_URL}/auth/login",
    "SCHEMA": f"{BASE_API_URL}/ride/metadata_mappings",
    "INSTRUCTOR": f"{BASE_API_URL}/instructor",
    "PROFILE": f"{BASE_API_URL}/me",
    "USER": f"{BASE_API_URL}/user",
    "USER_RELATIVE": {
        "FOLLOWERS": "followers",
        "FOLLOWING": "following",
        "ACHIEVEMENTS": "achievements",
        "WORKOUTS": "workouts",
    },
    "WORKOUT_DETAIL": f"{BASE_API_URL}/workout",
    "WORKOUT_RELATIVE": {
        "METRICS": "performance_graph",
        "ACHIEVEMENTS": "achievements",
        "SUMMARY": "summary",
    },
    "RIDE_DETAIL": f"{BASE_API_URL}/ride",
    "RIDES": f"{BASE_API_URL}/v2/ride/archived?browse_category=",
}
