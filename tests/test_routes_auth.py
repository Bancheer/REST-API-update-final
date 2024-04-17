from unittest.mock import Mock

import pytest
from src.conf import messages as msg
from fastapi import status

new_test_user = {
    "username": "agent007",
    "email": "agent007@example.com",
    "password": "12345678"
}

real_user = {
    "username": "Banch",
    "email": "banch@gmail.com",
    "password": "567234"
}


def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post("api/auth/signup", json=new_test_user)
    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert data["username"] == new_test_user["username"]
    assert data["email"] == new_test_user["email"]
    assert new_test_user["password"] not in data
    assert "avatar" in data


def test_signup_existing_email(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post("api/auth/signup", json=real_user)
    assert response.status_code == status.HTTP_201_CREATED, response.text
    assert response.json() == {"detail": msg.ACCOUNT_EXISTS}


def test_login_not_confirmed(client):
    response = client.post("api/auth/login",
                           data={"username": new_test_user["email"], "password": new_test_user["password"]})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    assert response.json() == {"detail": msg.ACCOUNT_NOT_CONFIRMED}


def test_request_email(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    response = client.post("/api/auth/request_email", json=new_test_user)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Check your email for confirmation."}


def test_request_email_open(client):
    username = "new_test_user"
    response = client.get(f"/api/auth/{username}")
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "image/png"
