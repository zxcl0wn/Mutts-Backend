# Аутентификация

## Обзор

API использует **JWT (JSON Web Tokens)** для аутентификации. Токены передаются через query параметр `access_token`.

---

## Регистрация

### `POST /auth/register`

Создать новый аккаунт.

**Request:**

```http
POST /auth/register HTTP/1.1
Content-Type: application/json

{
  "username": "player1",
  "password": "password123"
}
```

**Response (201 Created):**

```json
{
  "id": 1,
  "username": "player1"
}
```

**Errors:**

- `400 Bad Request` - Пользователь уже существует
- `422 Unprocessable Entity` - Невалидные данные

---

## Логин

### `POST /auth/login`

Получить JWT токены.

**Request:**

```http
POST /auth/login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=player1&password=password123
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:**

- `401 Unauthorized` - Неверный логин или пароль

---

## Refresh Token

### `POST /auth/refresh`

Обновить access токен используя refresh токен.

**Request:**

```http
POST /auth/refresh HTTP/1.1
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:**

- `401 Unauthorized` - Невалидный refresh токен

---

## Использование токенов

### Query параметр (рекомендуется для WebSocket)

```
ws://localhost:8000/ws/game/{game_id}?access_token={token}
```

```
http://localhost:8000/matchmaking/join?access_token={token}
```

### Authorization header (альтернатива)

```http
GET /api/endpoint HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Время жизни токенов

- **Access Token:** 30 минут
- **Refresh Token:** 30 дней

---

## JWT Payload

Access токен содержит:

```json
{
  "type": "access",
  "sub": "player1",
  "exp": 1746432000
}
```

- `type` - тип токена (`access` или `refresh`)
- `sub` - username пользователя
- `exp` - время истечения (Unix timestamp)

---

## Примеры

### JavaScript (Fetch API)

```javascript
// Логин
const response = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: 'username=player1&password=password123'
});

const data = await response.json();
const accessToken = data.access_token;

// Сохранить токен
localStorage.setItem('access_token', accessToken);

// Использовать токен
const gameResponse = await fetch(
  `http://localhost:8000/matchmaking/join?access_token=${accessToken}`,
  { method: 'POST' }
);
```

### JavaScript (WebSocket)

```javascript
const token = localStorage.getItem('access_token');
const ws = new WebSocket(
  `ws://localhost:8000/ws/game/${gameId}?access_token=${token}`
);
```
