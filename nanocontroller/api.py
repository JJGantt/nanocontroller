import functools
import inspect
import logging

import httpx
import requests

logger = logging.getLogger(__name__)

# Request failures are logged and the call returns None. The async methods use
# httpx and the sync ones requests, so both libraries' errors are handled, and
# the async wrapper awaits the call: a plain wrapper would hand back the
# coroutine before it runs, so nothing it raised could ever be caught here.
API_ERRORS = (httpx.HTTPError, requests.exceptions.RequestException)


def _log_error(err):
    if isinstance(err, (httpx.HTTPStatusError, requests.exceptions.HTTPError)):
        logger.error(f"HTTP error occurred: {err}")
    elif isinstance(err, API_ERRORS):
        logger.error(f"Request error occurred: {err}")
    else:
        logger.error(f"Unexpected error: {err}")


def handle_api_errors(func):
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as err:
                _log_error(err)
            return None
        return async_wrapper

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            _log_error(err)
        return None
    return wrapper

class NanoAPI:
    def __init__(self, auth_token, ip_address, port):
        self.auth_token = auth_token
        self.ip_address = ip_address
        self.port = port

    @property
    def base_url(self):
        return f"http://{self.ip_address}:{self.port}/api/v1/{self.auth_token}"
    
    @handle_api_errors
    def get_auth_token(self):
        url = f"http://{self.ip_address}:{self.port}/api/v1/new"

        response = requests.post(url)
        response.raise_for_status()
        self.auth_token = response.json()["auth_token"]

        return self.auth_token

    @handle_api_errors
    def get_layout(self):
        url = f"{self.base_url}/panelLayout/layout"

        response = requests.get(url)
        response.raise_for_status()  
        layout = response.json()
        return layout
    
    @handle_api_errors
    async def get_state(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/state")
        response.raise_for_status()
        state = response.json()

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/effects")
        response.raise_for_status()
        effects = response.json()

        return state, effects
    
    @handle_api_errors
    async def set_effect(self, effect):
        url = f"{self.base_url}/effects/select"
        payload = {'select': effect}
        async with httpx.AsyncClient() as client:
            response = await client.put(url, json=payload)
        response.raise_for_status()
        return response
    
    @handle_api_errors
    async def set_brightness(self, brightness, duration=2):
        url = f"{self.base_url}/state"
        payload = {'brightness': {'value': brightness, 'duration': duration}}
        async with httpx.AsyncClient() as client:
            response = await client.put(url, json=payload)
        response.raise_for_status()
        return response
    
    @handle_api_errors
    async def set_color(self):
        pass

    @handle_api_errors
    async def set_hue(self):
        pass

    @handle_api_errors
    async def set_saturation(self):
        pass

    @handle_api_errors
    async def custom(self, animation_string, loop):
        url = f"{self.base_url}/effects"
        payload = {"write" : {"command" : "display", "animType" : "custom", "animData" : animation_string, "loop": loop, "palette":[]}}
        
        async with httpx.AsyncClient() as client:
            response = await client.put(url, json=payload)
        response.raise_for_status()
        return response
    



