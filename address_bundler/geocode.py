"""
Geocoding utilities for address-bundler.

Run ``geocode_missing_students()`` to locate every ``Student`` with
``latitude`` or ``longitude`` still NULL, normalise the address, geocode
it, and persist results.

Designed for Nominatim + U.S. addresses.
"""

from __future__ import annotations

import logging
import random
import re
import time
from typing import Tuple, Optional

from tqdm import tqdm
from geopy.exc import (
    GeocoderQuotaExceeded,
    GeocoderServiceError,
    GeocoderTimedOut,
)
from geopy.geocoders import Nominatim

from common.models import Student

logger = logging.getLogger(__name__)

# ---------- Geocoder setup -------------------------------------------------

_GEOCODER: Nominatim | None = None


def _get_geolocator() -> Nominatim:
    """Singleton for the geopy Nominatim geocoder."""
    global _GEOCODER
    if _GEOCODER is None:
        _GEOCODER = Nominatim(user_agent="address_bundler/1.0", timeout=30)
    return _GEOCODER


# ---------- Address normalisation -----------------------------------------


_NORMALISATION_PATTERNS = [
    # Remove common apartment/unit designators – case-insensitive
    r"\s*,?\s*(Apt|Apartment|Unit|Suite|Ste|#)\s*[A-Za-z0-9\-]+",
    # Strip trailing ", USA" or ", United States"
    r",\s*USA$",
    r",\s*United States$",
]


def normalise_address(address: str) -> str:
    """Remove apartment/suite markers and other noise from a US address."""
    cleaned = address.strip()
    for pattern in _NORMALISATION_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


# ---------- Single-address geocode with retry ------------------------------


def geocode_address(
    address: str, max_retries: int = 5
) -> Tuple[Optional[float], Optional[float]]:
    """
    Geocode a single address.

    Returns (lat, lon) or (None, None) on failure.
    Retries with exponential back-off on quota/time-out style errors.
    """
    locator = _get_geolocator()
    query = normalise_address(address)

    for attempt in range(max_retries):
        try:
            location = locator.geocode(
                query,
                exactly_one=True,
                country_codes="us",  # bias to US
                addressdetails=False,
            )
            if location:
                return location.latitude, location.longitude
            # No result is not retry-able; break early
            logger.warning("No geocode result for '%s'", query)
            break
        except (GeocoderQuotaExceeded, GeocoderTimedOut, GeocoderServiceError) as e:
            wait = 2**attempt + random.uniform(0.0, 1.0)
            logger.info(
                "Geocode error '%s' (attempt %s/%s). Retrying in %.1fs",
                e,
                attempt + 1,
                max_retries,
                wait,
            )
            time.sleep(wait)
            continue
        except Exception as e:  # pragma: no cover
            logger.exception("Unexpected geocode exception for '%s': %s", query, e)
            break

    return None, None


# ---------- Batch runner ---------------------------------------------------


def geocode_missing_students() -> Tuple[int, int]:
    """
    Geocode every Student missing latitude/longitude.

    Returns (total_addresses_attempted, successfully_geocoded).
    """
    to_fix = Student.select().where(
        (Student.latitude.is_null(True)) | (Student.longitude.is_null(True))
    )

    total = to_fix.count()
    success = 0

    for student in tqdm(to_fix, total=total, unit="student"):
        lat, lon = geocode_address(student.address)
        if lat is not None and lon is not None:
            student.latitude = lat
            student.longitude = lon
            student.save(only=[Student.latitude, Student.longitude])
            success += 1

    return total, success
