# REST API

## Обзор

REST эндпоинты для аутентификации и матчмейкинга. Все игровые действия выполняются через WebSocket.

---

## Аутентификация

### `POST /auth/register`

Регистрация нового пользователя.

**Request:**
```json
{
  "username": "player1",
  "password": "password123"
}
```

**Response (201):**
```json
{
  "id": 1,
  "username": "player1"
}
```

---

### `POST /auth/login`

Логин и получение JWT токенов.

**Request (form-urlencoded):**
```
username=player1&password=password123
```

**Response (200):**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

---

### `POST /auth/refresh`

Обновление access токена.

**Request:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

---

## Матчмейкинг

### `POST /matchmaking/join`

Присоединиться к очереди матчмейкинга.

**Auth:** Требуется `access_token`

**Request:**
```http
POST /matchmaking/join?access_token={token}
```

**Response (200):**
```json
{
  "status": "queued",
  "message": "Added to matchmaking queue"
}
```

**Поведение:**
- Игрок добавляется в очередь
- Когда находится 2 игрока, автоматически создается игра
- Игроки получают `game_id` и могут подключиться через WebSocket

**Errors:**
- `401 Unauthorized` - Невалидный токен
- `400 Bad Request` - Игрок уже в игре

---

### `POST /matchmaking/leave`

Покинуть очередь матчмейкинга.

**Auth:** Требуется `access_token`

**Request:**
```http
POST /matchmaking/leave?access_token={token}
```

**Response (200):**
```json
{
  "status": "left",
  "message": "Removed from matchmaking queue"
}
```

---

## Swagger UI

Интерактивная документация доступна по адресу:

```
http://localhost:8000/docs
```

---

## Примеры

### cURL

```bash
# Регистрация
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"player1","password":"password123"}'

# Логин
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=player1&password=password123"

# Матчмейкинг
curl -X POST "http://localhost:8000/matchmaking/join?access_token=eyJhbGc..."
```

### JavaScript (Fetch)

```javascript
// Регистрация
const register = async (username, password) => {
  const response = await fetch('http://localhost:8000/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  return response.json();
};

// Логин
const login = async (username, password) => {
  const response = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `username=${username}&password=${password}`
  });
  return response.json();
};

// Матчмейкинг
const joinMatchmaking = async (token) => {
  const response = await fetch(
    `http://localhost:8000/matchmaking/join?access_token=${token}`,
    { method: 'POST' }
  );
  return response.json();
};
```

### Python (requests)

```python
import requests

# Регистрация
response = requests.post(
    'http://localhost:8000/auth/register',
    json={'username': 'player1', 'password': 'password123'}
)

# Логин
response = requests.post(
    'http://localhost:8000/auth/login',
    data={'username': 'player1', 'password': 'password123'}
)
token = response.json()['access_token']

# Матчмейкинг
response = requests.post(
    f'http://localhost:8000/matchmaking/join?access_token={token}'
)
```
