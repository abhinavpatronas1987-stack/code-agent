"""API Testing - Feature 27.

Simple HTTP client for API testing:
- Make HTTP requests
- Save and replay requests
- Environment variables
- Response validation
"""

import json
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class HttpMethod(Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class HttpRequest:
    """An HTTP request."""
    method: HttpMethod
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    params: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["method"] = self.method.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HttpRequest":
        data["method"] = HttpMethod(data["method"])
        return cls(**data)


@dataclass
class HttpResponse:
    """An HTTP response."""
    status_code: int
    status_text: str
    headers: Dict[str, str]
    body: str
    elapsed_time: float  # seconds
    size: int  # bytes

    @property
    def json(self) -> Optional[Any]:
        """Parse body as JSON."""
        try:
            return json.loads(self.body)
        except json.JSONDecodeError:
            return None

    @property
    def is_success(self) -> bool:
        """Check if response is successful (2xx)."""
        return 200 <= self.status_code < 300


@dataclass
class SavedRequest:
    """A saved request for replay."""
    id: str
    name: str
    request: HttpRequest
    description: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "request": self.request.to_dict(),
            "description": self.description,
            "tags": self.tags,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SavedRequest":
        data["request"] = HttpRequest.from_dict(data["request"])
        return cls(**data)


class ApiTester:
    """API testing utilities."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize API tester."""
        self.storage_dir = storage_dir or Path.home() / ".code-agent" / "api"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.requests_file = self.storage_dir / "requests.json"
        self.env_file = self.storage_dir / "env.json"
        self.saved_requests: Dict[str, SavedRequest] = {}
        self.environment: Dict[str, str] = {}
        self._load()

    def _load(self):
        """Load saved requests and environment."""
        if self.requests_file.exists():
            try:
                data = json.loads(self.requests_file.read_text(encoding="utf-8"))
                for req_data in data.get("requests", []):
                    saved = SavedRequest.from_dict(req_data)
                    self.saved_requests[saved.id] = saved
            except Exception:
                pass

        if self.env_file.exists():
            try:
                self.environment = json.loads(self.env_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    def _save(self):
        """Save requests and environment."""
        data = {
            "version": "1.0",
            "requests": [r.to_dict() for r in self.saved_requests.values()],
        }
        self.requests_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.env_file.write_text(json.dumps(self.environment, indent=2), encoding="utf-8")

    def _apply_environment(self, text: str) -> str:
        """Replace environment variables in text."""
        for key, value in self.environment.items():
            text = text.replace(f"{{{{{key}}}}}", value)
            text = text.replace(f"${{{key}}}", value)
        return text

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        params: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ) -> HttpResponse:
        """
        Make an HTTP request.

        Args:
            method: HTTP method
            url: URL to request
            headers: Request headers
            body: Request body
            params: Query parameters
            timeout: Timeout in seconds

        Returns:
            HttpResponse
        """
        # Apply environment variables
        url = self._apply_environment(url)
        if body:
            body = self._apply_environment(body)

        headers = headers or {}
        for key, value in headers.items():
            headers[key] = self._apply_environment(value)

        # Add query parameters
        if params:
            applied_params = {k: self._apply_environment(v) for k, v in params.items()}
            query_string = urllib.parse.urlencode(applied_params)
            url = f"{url}?{query_string}" if "?" not in url else f"{url}&{query_string}"

        # Prepare request
        req = urllib.request.Request(
            url,
            data=body.encode("utf-8") if body else None,
            headers=headers,
            method=method.upper(),
        )

        # Make request
        start_time = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_body = response.read().decode("utf-8", errors="ignore")
                elapsed = time.time() - start_time

                return HttpResponse(
                    status_code=response.status,
                    status_text=response.reason,
                    headers=dict(response.headers),
                    body=response_body,
                    elapsed_time=elapsed,
                    size=len(response_body),
                )

        except urllib.error.HTTPError as e:
            elapsed = time.time() - start_time
            body_text = ""
            try:
                body_text = e.read().decode("utf-8", errors="ignore")
            except:
                pass

            return HttpResponse(
                status_code=e.code,
                status_text=e.reason,
                headers=dict(e.headers) if e.headers else {},
                body=body_text,
                elapsed_time=elapsed,
                size=len(body_text),
            )

        except urllib.error.URLError as e:
            elapsed = time.time() - start_time
            return HttpResponse(
                status_code=0,
                status_text=str(e.reason),
                headers={},
                body="",
                elapsed_time=elapsed,
                size=0,
            )

        except Exception as e:
            elapsed = time.time() - start_time
            return HttpResponse(
                status_code=0,
                status_text=str(e),
                headers={},
                body="",
                elapsed_time=elapsed,
                size=0,
            )

    def get(self, url: str, **kwargs) -> HttpResponse:
        """Make GET request."""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, body: Optional[str] = None, **kwargs) -> HttpResponse:
        """Make POST request."""
        return self.request("POST", url, body=body, **kwargs)

    def put(self, url: str, body: Optional[str] = None, **kwargs) -> HttpResponse:
        """Make PUT request."""
        return self.request("PUT", url, body=body, **kwargs)

    def delete(self, url: str, **kwargs) -> HttpResponse:
        """Make DELETE request."""
        return self.request("DELETE", url, **kwargs)

    def save_request(
        self,
        name: str,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> SavedRequest:
        """Save a request for later replay."""
        import hashlib

        req_id = hashlib.md5(f"{name}:{datetime.now().isoformat()}".encode()).hexdigest()[:8]

        saved = SavedRequest(
            id=req_id,
            name=name,
            request=HttpRequest(
                method=HttpMethod(method.upper()),
                url=url,
                headers=headers or {},
                body=body,
            ),
            description=description,
            tags=tags or [],
            created_at=datetime.now().isoformat(),
        )

        self.saved_requests[req_id] = saved
        self._save()

        return saved

    def replay(self, request_id: str) -> Optional[HttpResponse]:
        """Replay a saved request."""
        saved = self.saved_requests.get(request_id)
        if not saved:
            return None

        req = saved.request
        return self.request(
            req.method.value,
            req.url,
            req.headers,
            req.body,
            req.params,
            req.timeout,
        )

    def list_saved(self, tags: Optional[List[str]] = None) -> List[SavedRequest]:
        """List saved requests."""
        results = list(self.saved_requests.values())

        if tags:
            tags_lower = [t.lower() for t in tags]
            results = [
                r for r in results
                if any(t.lower() in tags_lower for t in r.tags)
            ]

        return results

    def delete_saved(self, request_id: str) -> bool:
        """Delete a saved request."""
        if request_id in self.saved_requests:
            del self.saved_requests[request_id]
            self._save()
            return True
        return False

    def set_env(self, key: str, value: str):
        """Set environment variable."""
        self.environment[key] = value
        self._save()

    def get_env(self, key: str) -> Optional[str]:
        """Get environment variable."""
        return self.environment.get(key)

    def list_env(self) -> Dict[str, str]:
        """List all environment variables."""
        return self.environment.copy()

    def delete_env(self, key: str) -> bool:
        """Delete environment variable."""
        if key in self.environment:
            del self.environment[key]
            self._save()
            return True
        return False

    def format_response(self, response: HttpResponse) -> str:
        """Format response for display."""
        lines = []
        lines.append("=" * 60)
        lines.append("  HTTP RESPONSE")
        lines.append("=" * 60)
        lines.append("")

        # Status
        status_color = "green" if response.is_success else "red"
        lines.append(f"Status: {response.status_code} {response.status_text}")
        lines.append(f"Time: {response.elapsed_time:.3f}s")
        lines.append(f"Size: {response.size} bytes")
        lines.append("")

        # Headers
        lines.append("Headers:")
        for key, value in list(response.headers.items())[:10]:
            lines.append(f"  {key}: {value[:50]}")
        lines.append("")

        # Body
        lines.append("Body:")
        if response.json:
            try:
                formatted = json.dumps(response.json, indent=2)
                lines.append(formatted[:2000])
                if len(formatted) > 2000:
                    lines.append("... (truncated)")
            except:
                lines.append(response.body[:2000])
        else:
            lines.append(response.body[:2000])
            if len(response.body) > 2000:
                lines.append("... (truncated)")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


# Global instance
_api_tester: Optional[ApiTester] = None


def get_api_tester() -> ApiTester:
    """Get or create API tester."""
    global _api_tester
    if _api_tester is None:
        _api_tester = ApiTester()
    return _api_tester


# Convenience functions
def http_get(url: str, **kwargs) -> HttpResponse:
    """Make GET request."""
    return get_api_tester().get(url, **kwargs)


def http_post(url: str, body: Optional[str] = None, **kwargs) -> HttpResponse:
    """Make POST request."""
    return get_api_tester().post(url, body, **kwargs)


def http_request(method: str, url: str, **kwargs) -> HttpResponse:
    """Make HTTP request."""
    return get_api_tester().request(method, url, **kwargs)
