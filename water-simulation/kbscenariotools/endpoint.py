import json
from argparse import Namespace
from typing import Optional, Tuple

import requests
from requests.auth import HTTPBasicAuth

EndpointResponse = Tuple[int, Optional[dict]]


class ScenarioManagerEndpoint:
    def __init__(
        self, endpoint: str, user: Optional[str] = None, password: Optional[str] = None
    ):
        self._auth = None
        if user is not None and password is not None:
            self._auth = HTTPBasicAuth(user, password)
        self._endpoint = endpoint if not endpoint.endswith("/") else endpoint[:-1]

    def request(
        self, method, path: str, data: dict = None, content_type: str = None
    ) -> EndpointResponse:
        if not path.startswith("/"):
            path = "/" + path
        headers = {
            "Content-Type": content_type,
        }
        response = requests.request(
            method,
            f"{self._endpoint}{path}",
            data=json.dumps(data),
            headers=headers,
            auth=self._auth,
        )
        status = response.status_code
        if 200 <= status <= 299:
            return status, response.json()
        return status, response.text

    def get(self, path: str = "/") -> EndpointResponse:
        return self.request(method="GET", path=path)

    def post(
        self, path: str, data: dict, content_type: str = "application/json"
    ) -> EndpointResponse:
        return self.request(
            method="POST", path=path, data=data, content_type=content_type
        )

    @classmethod
    def from_args(cls, args: Namespace) -> "ScenarioManagerEndpoint":
        return cls(endpoint=args.endpoint, user=args.user, password=args.password)
