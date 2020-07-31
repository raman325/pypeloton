from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Union

from aiohttp import ClientResponseError, ClientSession

from .const import ENDPOINTS, HEADERS
from .helpers import get_workout_params
from .utils import async_to_sync

_LOGGER = logging.getLogger(__name__)


class PelotonResponseException(Exception):
    def __init__(self, response):
        super(PelotonResponseException, self).__init__(
            self, "Unable to handle response"
        )
        self.response = response


class PelotonAsync:
    """Async Peloton client."""
    def __init__(
        self,
        username_or_email: str,
        password: str,
        page_limit: int = 100,
        session: ClientSession = None,
        log_level: Union[int, str] = logging.WARNING,
    ) -> None:
        """Initialize Peloton API Client instance."""
        self.username_or_email = username_or_email
        self.user_id = None
        self.username = None
        self.email = None
        self.name = None
        self._password = password
        self._session_expiration = None
        self._session = session
        self._cookies = None

        _LOGGER.setLevel(log_level)
        self._page_limit = page_limit

    async def _login(self, session: ClientSession) -> None:
        """Log in to Peloton API to get proper cookies."""
        resp = await session.post(
            ENDPOINTS["LOGIN"],
            json={
                "username_or_email": self.username_or_email,
                "password": self._password,
            },
            headers=HEADERS,
            raise_for_status=True,
        )

        # Set session expiration and store cookies for next time
        session_max_age = int(resp.cookies["peloton_session_id"]["max-age"])
        self._session_expiration = datetime.now() - timedelta(
            seconds=(session_max_age - 2)
        )
        self._cookies = resp.cookies

        json_resp = await resp.json()
        self.user_id = json_resp["user_id"]
        self.username = json_resp["user_data"]["username"]
        self.email = json_resp["user_data"]["email"]
        self.name = json_resp["user_data"]["name"]

    async def _call_api(
        self, url: str, params: Dict[str, Any] = None, data: Any = None
    ):
        """Call unpaginated peloton API."""
        if not params:
            params = {}
        params.update({"limit": self._page_limit})

        try:
            if self._session:
                # Only login again if a valid session exists
                if (
                    not self._session_expiration
                    or self._session_expiration > datetime.now()
                ):
                    await self._login(self._session)
                resp = await self._session.get(
                    url, params=params, json=data, headers=HEADERS, raise_for_status=True
                )
                return await resp.json()

            else:
                async with ClientSession() as session:
                    # Only login again if a valid session exists
                    if (
                        not self._session_expiration
                        or self._session_expiration > datetime.now()
                    ):
                        await self._login(session)
                    # Restore saved cookies to session since we are creating a new session each time
                    session.cookie_jar.update_cookies(self._cookies)
                    resp = await session.get(
                        url,
                        params=params,
                        json=data,
                        headers=HEADERS,
                        raise_for_status=True,
                    )
                    return await resp.json()
        except ClientResponseError as e:
            raise PelotonResponseException(f"{e.status}: {e.message}")

    async def _get_paginated_results(
        self,
        url: str,
        key: str,
        num_results: int = 0,
        params: Dict[str, Any] = None,
        data: Any = None,
    ):
        """Call paginated peloton API, combining results into a single payload."""
        if not params:
            params = {}
        curr_page = 0
        num_pages = None
        all_results = []
        while num_pages is None or (
            curr_page < num_pages
            and (not num_results or len(all_results) < num_results)
        ):
            params.update({"page": curr_page})
            results = await self._call_api(url, params, data)
            if "page_count" in results and key in results:
                num_pages = results["page_count"]
                all_results += results[key]
            else:
                raise PelotonResponseException(results)
            curr_page += 1

        if num_results:
            return all_results[:num_results]

        return all_results

    async def get_instructors(self) -> List[Dict[str, Any]]:
        """Get a list of all instructors."""
        return await self._get_paginated_results(ENDPOINTS["INSTRUCTOR"], "data")

    async def get_user_id(self, username: str) -> Dict[str, Any]:
        """Get a given user's user ID. Useful for other functions."""
        resp = await self._call_api(f"{ENDPOINTS['USER']}/{username}")
        return resp["id"]

    async def get_my_profile(self) -> Dict[str, Any]:
        """Get the profile of the logged in user."""
        return await self._call_api(ENDPOINTS["PROFILE"])

    async def get_user_detail(self, user_id: str = None) -> Dict[str, Any]:
        """Get the profile of a user."""
        if not user_id:
            user_id = self.user_id
        return await self._call_api(f"{ENDPOINTS['USER']}/{user_id}")

    async def get_user_followers(self, user_id: str = None) -> Dict[str, Any]:
        """Get the list of followers of a user."""
        if not user_id:
            user_id = self.user_id
        return await self._call_api(
            f"{ENDPOINTS['USER']}/{user_id}/{ENDPOINTS['USER_RELATIVE']['FOLLOWERS']}"
        )

    async def get_user_following(self, user_id: str = None) -> Dict[str, Any]:
        """Get the list of users that a user is following."""
        if not user_id:
            user_id = self.user_id
        return await self._call_api(
            f"{ENDPOINTS['USER']}/{user_id}/{ENDPOINTS['USER_RELATIVE']['FOLLOWING']}"
        )

    async def get_user_achievements(self, user_id: str = None) -> Dict[str, Any]:
        """Get the list of achievements for a user."""
        if not user_id:
            user_id = self.user_id
        return await self._call_api(
            f"{ENDPOINTS['USER']}/{user_id}/{ENDPOINTS['USER_RELATIVE']['ACHIEVEMENTS']}"
        )

    async def get_user_workouts(
        self,
        user_id: str = None,
        num_latest_workouts: int = 0,
        include_ride_details: bool = False,
        include_instructor_details: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get list of worksouts for a given user."""
        params = get_workout_params(include_ride_details, include_instructor_details)
        if not user_id:
            user_id = self.user_id
        return await self._get_paginated_results(
            f"{ENDPOINTS['USER']}/{user_id}/{ENDPOINTS['USER_RELATIVE']['WORKOUTS']}",
            "data",
            num_results=num_latest_workouts,
            params=params,
        )

    async def get_workout_metadata(
        self,
        workout_id: str,
        include_ride_details: bool = False,
        include_instructor_details: bool = False,
    ) -> Dict[str, Any]:
        """Get metadata for a given workout."""
        params = get_workout_params(include_ride_details, include_instructor_details)
        return await self._call_api(
            f"{ENDPOINTS['WORKOUT_DETAIL']}/{workout_id}", params=params
        )

    async def get_workout_metrics(self, workout_id: str, frequency_sec: int = 10):
        """Get metrics for a given workout."""
        return await self._call_api(
            f"{ENDPOINTS['WORKOUT_DETAIL']}/{workout_id}/{ENDPOINTS['WORKOUT_RELATIVE']['METRICS']}",
            params={"every_n": frequency_sec},
        )

    async def get_workout_achievements(self, workout_id: str):
        """Get achievements for a given workout."""
        return await self._call_api(
            f"{ENDPOINTS['WORKOUT_DETAIL']}/{workout_id}/{ENDPOINTS['WORKOUT_RELATIVE']['ACHIEVEMENTS']}"
        )

    async def get_workout_summary(self, workout_id: str):
        """Get summary of a given workout."""
        return await self._call_api(
            f"{ENDPOINTS['WORKOUT_DETAIL']}/{workout_id}/{ENDPOINTS['WORKOUT_RELATIVE']['SUMMARY']}"
        )

    async def get_ride_metadata(self, ride_id: str) -> Dict[str, Any]:
        """Get metadata for a given ride."""
        return await self._call_api(f"{ENDPOINTS['RIDE_DETAIL']}/{ride_id}")

    async def get_schema(self) -> Dict[str, Any]:
        """Get API schema."""
        return await self._call_api(f"{ENDPOINTS['SCHEMA']}")


class Peloton(PelotonAsync):
    def __init__(
        self,
        username_or_email: str,
        password: str,
        page_limit: int = 5,
        log_level: Union[int, str] = logging.WARNING,
    ) -> None:
        super(Peloton, self).__init__(
            username_or_email, password, page_limit=page_limit, log_level=log_level
        )

    @async_to_sync
    async def get_instructors(self):
        return await super(Peloton, self).get_instructors()

    @async_to_sync
    async def get_user_id(self, username: str) -> Dict[str, Any]:
        return await super(Peloton, self).get_user_id(username)

    @async_to_sync
    async def get_my_profile(self) -> Dict[str, Any]:
        return await super(Peloton, self).get_my_profile()

    @async_to_sync
    async def get_user_detail(self, user_id: str = None) -> Dict[str, Any]:
        return await super(Peloton, self).get_user_detail(user_id)

    @async_to_sync
    async def get_user_followers(self, user_id: str = None) -> Dict[str, Any]:
        return await super(Peloton, self).get_user_followers(user_id)

    @async_to_sync
    async def get_user_following(self, user_id: str = None) -> Dict[str, Any]:
        return await super(Peloton, self).get_user_following(user_id)

    @async_to_sync
    async def get_user_achievements(self, user_id: str = None) -> Dict[str, Any]:
        return await super(Peloton, self).get_user_achievements(user_id)

    @async_to_sync
    async def get_user_workouts(
        self,
        user_id: str = None,
        num_latest_workouts: int = 0,
        include_ride_details: bool = False,
        include_instructor_details: bool = False,
    ) -> List[Dict[str, Any]]:
        return await super(Peloton, self).get_user_workouts(
            user_id, num_latest_workouts, include_ride_details, include_instructor_details
        )

    @async_to_sync
    async def get_workout_metadata(
        self,
        workout_id: str,
        include_ride_details: bool = False,
        include_instructor_details: bool = False,
    ) -> Dict[str, Any]:
        return await super(Peloton, self).get_workout_metadata(
            workout_id, include_ride_details, include_instructor_details
        )

    @async_to_sync
    async def get_workout_metrics(self, workout_id: str, frequency_sec: int = 10):
        return await super(Peloton, self).get_workout_metrics(workout_id, frequency_sec)

    @async_to_sync
    async def get_workout_achievements(self, workout_id: str):
        return await super(Peloton, self).get_workout_achievements(workout_id)

    @async_to_sync
    async def get_workout_summary(self, workout_id: str):
        return await super(Peloton, self).get_workout_summary(workout_id)

    @async_to_sync
    async def get_ride_metadata(self, ride_id: str) -> Dict[str, Any]:
        return await super(Peloton, self).get_ride_metadata(ride_id)

    @async_to_sync
    async def get_schema(self) -> Dict[str, Any]:
        return await super(Peloton, self).get_schema()
