from __future__ import annotations

from typing import Any

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class GeoapifyError(Exception):
    pass


class GeoapifyClient:
    base_url = "https://api.geoapify.com/v1/geocode"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def geocode(self, text: str) -> dict[str, Any]:
        data = self._request("search", {"text": text, "format": "json", "limit": 1})
        results = data.get("results", [])
        if not results:
            raise GeoapifyError(f"No se encontraron resultados para '{text}'.")

        result = results[0]
        return {
            "formatted_address": result["formatted"],
            "address_line1": result.get("address_line1") or result["formatted"],
            "address_line2": result.get("address_line2", ""),
            "latitude": result["lat"],
            "longitude": result["lon"],
            "country_code": result.get("country_code", ""),
        }

    def autocomplete(
        self,
        text: str,
        *,
        limit: int = 5,
        country_bias: str = "",
        country_filter: str = "",
        city_bias: str = "",
        proximity: tuple[float, float] | None = None,
    ) -> list[dict[str, Any]]:
        if not text.strip():
            return []

        params = {
            "text": text,
            "format": "json",
            "limit": limit,
            "lang": settings.GEOAPIFY_AUTOCOMPLETE_LANG,
        }

        selected_country_bias = country_bias or settings.GEOAPIFY_AUTOCOMPLETE_COUNTRY_BIAS
        selected_country_filter = country_filter or settings.GEOAPIFY_AUTOCOMPLETE_COUNTRY_FILTER
        bias_values = []

        if proximity:
            lon, lat = proximity
            bias_values.append(f"proximity:{lon},{lat}")

        if selected_country_bias:
            bias_values.append(f"countrycode:{selected_country_bias}")

        if bias_values:
            params["bias"] = "|".join(bias_values)

        if selected_country_filter:
            params["filter"] = f"countrycode:{selected_country_filter}"

        data = self._request("autocomplete", params)
        results = [
            {
                "formatted_address": result["formatted"],
                "address_line1": result.get("address_line1") or result["formatted"],
                "address_line2": result.get("address_line2", ""),
                "latitude": result["lat"],
                "longitude": result["lon"],
                "result_type": result.get("result_type", ""),
                "match_type": result.get("rank", {}).get("match_type", ""),
                "confidence": result.get("rank", {}).get("confidence", 0),
                "country_code": result.get("country_code", ""),
            }
            for result in data.get("results", [])
        ]
        return self._rank_autocomplete_results(text, results, city_bias=city_bias)

    def _rank_autocomplete_results(
        self,
        text: str,
        results: list[dict[str, Any]],
        *,
        city_bias: str = "",
    ) -> list[dict[str, Any]]:
        query = text.strip().lower()
        preferred_city = city_bias.strip().lower()

        def score(result: dict[str, Any]) -> tuple[float, float, int]:
            line1 = result["address_line1"].lower()
            formatted = result["formatted_address"].lower()
            starts = 1 if line1.startswith(query) or formatted.startswith(query) else 0
            contains = 1 if query in line1 or query in formatted else 0
            confidence = float(result.get("confidence", 0))
            preferred_type = 1 if result.get("result_type") in {"amenity", "building", "street"} else 0
            city_match = 1 if preferred_city and preferred_city in formatted else 0
            return (starts, city_match, contains + preferred_type, confidence)

        ranked = sorted(results, key=score, reverse=True)
        return ranked

    def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                params={**params, "apiKey": self.api_key},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise GeoapifyError("No fue posible consultar Geoapify en este momento.") from exc

        return response.json()


def get_geocoding_client() -> GeoapifyClient:
    if not settings.GEOAPIFY_API_KEY:
        raise ImproperlyConfigured("GEOAPIFY_API_KEY is not configured.")

    return GeoapifyClient(settings.GEOAPIFY_API_KEY)
