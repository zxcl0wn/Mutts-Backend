# Mutts API Documentation

## Содержание

- [Аутентификация](AUTHENTICATION.md) - JWT токены, регистрация, логин
- [REST API](REST_API.md) - HTTP эндпоинты
- [WebSocket API](WEBSOCKET_API.md) - WS протокол
- [Игровой процесс](GAME_FLOW.md) - Как работает игра
- [Система боя](BATTLE_SYSTEM.md) - Координаты, атаки, механики

## Быстрый старт

### 1. Регистрация и логин

```bash
# Регистрация
POST http://193.53.40.62:8000/auth/register
Content-Type: application/json

{
  "username": "player1",
  "password": "password123"
}

# Логин
POST http://193.53.40.62:8000/auth/login
Content-Type: application/x-www-form-urlencoded

username=player1&password=password123

# Ответ:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### 2. Матчмейкинг

```bash
POST http://193.53.40.62:8000/matchmaking/join?access_token={token}

# Через 1-2 секунды игра создастся автоматически
```

### 3. Подключение к игре через WebSocket

```javascript
const ws = new WebSocket(
  `ws://193.53.40.62:8000/ws/game/{game_id}?access_token={token}`
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

### 4. Покупка юнита

```javascript
ws.send(JSON.stringify({
  type: "place_unit",
  unit_type: "warrior"
}));
```

## Технологии

- **Backend:** FastAPI (Python)
- **WebSocket:** FastAPI WebSocket
- **Database:** PostgreSQL
- **Cache:** Redis
- **Auth:** JWT
