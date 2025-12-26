import pytest
import requests
import requests_mock
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crypto_mcp import (
    safe_api_call, get_cached_data, set_cached_data, clear_expired_cache,
    CryptoAPIError, APIRateLimitError, APINetworkError, APIDataError
)


class TestSafeApiCall:
    """Test cases for the safe_api_call function."""

    def test_successful_api_call(self):
        """Test successful API call with caching."""
        with requests_mock.Mocker() as m:
            url = "https://api.example.com/test"
            mock_data = {"price": 50000}

            m.get(url, json=mock_data)

            result = safe_api_call(url, "TestAPI")

            assert result == mock_data
            # Check if data was cached
            cached = get_cached_data(url)
            assert cached == mock_data

    def test_rate_limit_error(self):
        """Test handling of rate limit errors."""
        # Clear any cached data
        from crypto_mcp import price_cache
        price_cache.clear()
        
        with requests_mock.Mocker() as m:
            url = "https://api.example.com/test"
            m.get(url, status_code=429, text="Rate limit exceeded")

            with pytest.raises(APIRateLimitError):
                safe_api_call(url, "TestAPI")

    def test_network_timeout_error(self):
        """Test handling of network timeout errors."""
        # Clear any cached data
        from crypto_mcp import price_cache
        price_cache.clear()
        
        with requests_mock.Mocker() as m:
            url = "https://api.example.com/test"
            m.get(url, exc=requests.exceptions.Timeout)

            with pytest.raises(APINetworkError):
                safe_api_call(url, "TestAPI")

    def test_http_error(self):
        """Test handling of HTTP errors."""
        # Clear any cached data
        from crypto_mcp import price_cache
        price_cache.clear()
        
        with requests_mock.Mocker() as m:
            url = "https://api.example.com/test"
            m.get(url, status_code=404, text="Not Found")

            with pytest.raises(CryptoAPIError):
                safe_api_call(url, "TestAPI")

    def test_invalid_json_error(self):
        """Test handling of invalid JSON responses."""
        # Clear any cached data
        from crypto_mcp import price_cache
        price_cache.clear()
        
        with requests_mock.Mocker() as m:
            url = "https://api.example.com/test"
            m.get(url, text="Invalid JSON")

            with pytest.raises(APIDataError):
                safe_api_call(url, "TestAPI")

    def test_cache_hit(self):
        """Test that cached data is returned without API call."""
        url = "https://api.example.com/cached"
        mock_data = {"cached": True}

        # Pre-populate cache
        set_cached_data(url, mock_data)

        # Call should return cached data without making HTTP request
        result = safe_api_call(url, "TestAPI", use_cache=True)

        assert result == mock_data

    def test_cache_disabled(self):
        """Test that cache can be disabled."""
        with requests_mock.Mocker() as m:
            url = "https://api.example.com/no-cache"
            mock_data = {"no_cache": True}

            m.get(url, json=mock_data)

            # Pre-populate cache
            set_cached_data(url, {"old": "data"})

            # Call with cache disabled should make HTTP request
            result = safe_api_call(url, "TestAPI", use_cache=False)

            assert result == mock_data
            # Should have made the HTTP call despite cache existing


class TestCacheManagement:
    """Test cases for cache management functions."""

    def test_cache_operations(self):
        """Test basic cache set/get operations."""
        url = "https://api.example.com/cache-test"
        data = {"test": "data"}

        # Initially no cache
        assert get_cached_data(url) is None

        # Set cache
        set_cached_data(url, data)

        # Get cache
        cached = get_cached_data(url)
        assert cached == data

    def test_cache_expiry(self):
        """Test cache expiry functionality."""
        url = "https://api.example.com/expiry-test"
        data = {"expires": True}

        # Mock time to control expiry
        with patch('crypto_mcp.time.time') as mock_time:
            # Set initial time
            mock_time.return_value = 1000

            set_cached_data(url, data)

            # Still valid (within 5 minutes)
            mock_time.return_value = 1000 + 299  # 299 seconds later
            assert get_cached_data(url) == data

            # Expired (after 5 minutes + 1 second)
            mock_time.return_value = 1000 + 301
            assert get_cached_data(url) is None

    def test_clear_expired_cache(self):
        """Test clearing of expired cache entries."""
        with patch('crypto_mcp.time.time') as mock_time:
            mock_time.return_value = 1000

            # Set multiple cache entries
            set_cached_data("url1", {"data": 1})
            set_cached_data("url2", {"data": 2})

            # Fast forward time to expire entries
            mock_time.return_value = 1000 + 400  # 400 seconds later

            # Clear expired entries
            clear_expired_cache()

            # Both should be cleared
            assert get_cached_data("url1") is None
            assert get_cached_data("url2") is None


if __name__ == "__main__":
    pytest.main([__file__])