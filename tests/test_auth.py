import pytest


@pytest.mark.asyncio
async def test_login_and_check_auth(async_client):
    # 1. Логинимся
    response = await async_client.post(
        "/login",
        json={"email": "test@usser.com", "password": "testpassword"}
    )

    assert response.status_code == 200
    assert "my_access_token" in response.cookies

    # 2. Проверяем доступ к /check-auth
    response2 = await async_client.get("/check-auth", cookies=response.cookies)

    assert response2.status_code == 200
    assert response2.json()["status"] == "ok"
