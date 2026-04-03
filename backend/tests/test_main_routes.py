from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Stock Portfolio API"
    assert response.json()["status"] == "running"


def test_health_check() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_stocks() -> None:
    response = client.get("/api/stocks/")
    assert response.status_code == 200
    stocks = response.json()
    assert isinstance(stocks, list)
    assert any(stock["symbol"] == "AAPL" for stock in stocks)


def test_get_stock_found() -> None:
    response = client.get("/api/stocks/AAPL")
    assert response.status_code == 200
    stock = response.json()
    assert stock["symbol"] == "AAPL"
    assert stock["name"] == "Apple Inc."


def test_get_stock_not_found() -> None:
    response = client.get("/api/stocks/INVALID")
    assert response.status_code == 404
    assert response.json()["detail"] == "Stock not found"
