from backend.config import Settings, get_settings


def test_get_settings_returns_settings_instance() -> None:
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert hasattr(settings, "api_host")
    assert hasattr(settings, "api_port")
    assert hasattr(settings, "debug")
    assert hasattr(settings, "stock_api_key")
    assert hasattr(settings, "stock_api_url")
