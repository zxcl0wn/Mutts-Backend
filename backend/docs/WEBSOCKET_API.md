# WebSocket API

## Обзор

WebSocket используется для реалтайм игрового взаимодействия. Все игровые действия (покупка юнитов, перемещение, бой и т.д.) происходят через WebSocket.

---

## Подключение

### URL

```
ws://localhost:8000/ws/game/{game_id}?access_token={token}
```

**Параметры:**
- `game_id` - ID игры (получается после матчмейкинга)
- `access_token` - JWT токен

### Пример (JavaScript)

```javascript
const gameId = "abc-123-def-456";
const token = localStorage.getItem('access_token');

const ws = new WebSocket(
  `ws://localhost:8000/ws/game/${gameId}?access_token=${token}`
);

ws.onopen = () => {
  console.log('Connected to game');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
  handleGameEvent(data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from game');
};
```

---

## События от сервера → клиент

### `countdown`

Обратный отсчет перед началом игры (3-2-1).

```json
{
  "type": "countdown",
  "seconds": 3
}
```

**Поля:**
- `seconds` - оставшиеся секунды (3, 2, 1)

---

### `planning_phase_start`

Начало фазы планирования.

```json
{
  "type": "planning_phase_start",
  "round": 1,
  "time_left": 20
}
```

**Поля:**
- `round` - номер раунда
- `time_left` - время фазы в секундах

---

### `unit_placed`

Юнит размещен на поле или скамейке.

```json
{
  "type": "unit_placed",
  "unit": {
    "id": "abc-123",
    "type": "warrior",
    "level": 1,
    "hp": 100,
    "max_hp": 100,
    "attack": 20,
    "attack_speed": 1.0,
    "range": 1,
    "move_speed": 2.0,
    "position_x": 2.5,
    "position_y": 1.5,
    "owner": "player1",
    "target_id": null,
    "location": "board",
    "crit_chance": 0.0,
    "crit_damage": 2.0
  },
  "player": "player1",
  "coins_left": 7
}
```

**Поля:**
- `unit` - полная информация о юните
- `player` - кто разместил юнита
- `coins_left` - оставшиеся монеты

---

### `auto_merge`

Автоматическое слияние юнитов (2 одинаковых → 1 улучшенный).

```json
{
  "type": "auto_merge",
  "merged_unit": {
    "id": "abcd123",
    "type": "warrior",
    "level": 2,
    "hp": 200,
    "max_hp": 200,
    "attack": 40,
    "attack_speed": 1,
    "range": 1,
    "move_speed": 2,
    "position_x": 0.5,
    "position_y": 5.5,
    "owner": "player1",
    "target_id": null,
    "location": "board",
    "last_attack_time": 0,
    "crit_chance": 0,
    "crit_damage": 2
  },
  "player": "player1",
  "coins_left": 20
}
```

---

### `unit_moved`

Юнит перемещен.

```json
{
  "type": "unit_moved",
  "unit_id": "abc-123",
  "x": 3.5,
  "y": 2.5,
  "location": "bench/board",
  "player": "player1"
}
```

---

### `unit_sold`

Юнит продан.

```json
{
  "type": "unit_sold",
  "unit_id": "abc-123",
  "player": "player1",
  "refund": 2,
  "coins_left": 9
}
```

**Поля:**
- `refund` - возврат монет (50% от стоимости)

---

### `battle_phase_start`

Начало фазы боя.

```json
{
  "type": "battle_phase_start",
  "round": 1
}
```

---

### `battle_events`

События боя для воспроизведения на клиенте.

```json
{
  "type": "battle_events",
  "events": [
    {
      "time": 0.0,
      "type": "battle_start"
    },
    {
      "time": 0.1,
      "type": "movement",
      "unit_id": "abc-123",
      "position": [2.7, 1.8]
    },
    {
      "time": 1.5,
      "type": "attack",
      "unit_id": "abc-123",
      "target_id": "def-456",
      "damage": 20,
      "crit": false
    },
    {
      "time": 3.5,
      "type": "death",
      "unit_id": "def-456"
    },
    {
      "time": 3.5,
      "type": "battle_end"
    }
  ]
}
```

**Типы событий:**
- `battle_start` - начало боя
- `movement` - юнит двигается
- `attack` - юнит атакует
- `death` - юнит умер
- `battle_end` - конец боя

**Воспроизведение:**
Клиент должен воспроизвести события по времени (`event.time * 1000` мс).

---

### `battle_phase_end`

Конец фазы боя, результаты раунда.

```json
{
  "type": "battle_phase_end",
  "round": 1,
  "round_winner": "player1",
  "damage_to_player1": 0,
  "damage_to_player2": 3,
  "player1_hp": 100,
  "player2_hp": 97
}
```

**Поля:**
- `round_winner` - победитель раунда (`"player1"`, `"player2"`, `"draw"`)
- `damage_to_playerX` - урон нанесенный игроку
- `playerX_hp` - оставшееся HP

---

### `game_over`

Игра завершена.

```json
{
  "type": "game_over",
  "winner": "player1",
  "player1_hp": 15,
  "player2_hp": -3
}
```

**Поля:**
- `winner` - победитель (`"player1"`, `"player2"`, `"draw"`)

---

## События от клиента → сервер

### `place_unit`

Купить и разместить юнита.

```json
{
  "type": "place_unit",
  "unit_type": "warrior"
}
```

**Параметры:**
- `unit_type` - тип юнита (`"warrior"`, `"archer"`, `"mage"`)

**Поведение:**
- Автоматически размещается на поле (если есть место)
- Если поле заполнено → размещается на скамейке
- Если 2 одинаковых юнита → автоматический мердж

**Стоимость:**
- Берется из БД

---

### `move_unit`

Переместить юнита.

```json
{
  "type": "move_unit",
  "unit_id": "abc-123",
  "x": 3,
  "y": 2,
  "location": "board"
}
```

**Параметры:**
- `unit_id` - ID юнита
- `x`, `y` - координаты клетки (0-6, 0-7)
- `location` - `"board"` или `"bench"`

**Ограничения:**
- Можно перемещать только своих юнитов
- Нельзя перемещать на занятую клетку
- Максимум 6 юнитов на поле, 4 на скамейке

---

### `sell_unit`

Продать юнита.

```json
{
  "type": "sell_unit",
  "unit_id": "abc-123"
}
```

**Возврат:**
- 50% от стоимости юнита (округление вниз)

---


**Требования:**
- Оба юнита одного типа
- Оба юнита одного уровня
- Уровень < 4 (максимальный уровень)

**Результат:**
- Два юнита удаляются
- Создается один юнит уровня +1

---

## Примеры использования

### Полный игровой цикл

```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/game/${gameId}?access_token=${token}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'countdown':
      showCountdown(data.seconds);
      break;
      
    case 'planning_phase_start':
      startPlanningPhase(data.round, data.time_left);
      break;
      
    case 'unit_placed':
      addUnitToBoard(data.unit);
      updateCoins(data.coins_left);
      break;
      
    case 'battle_phase_start':
      startBattlePhase();
      break;
      
    case 'battle_events':
      replayBattle(data.events);
      break;
      
    case 'battle_phase_end':
      showBattleResults(data);
      break;
      
    case 'game_over':
      showGameOver(data.winner);
      break;
  }
};

// Купить юнита
function buyUnit(unitType) {
  ws.send(JSON.stringify({
    type: 'place_unit',
    unit_type: unitType
  }));
}

// Переместить юнита
function moveUnit(unitId, x, y, location) {
  ws.send(JSON.stringify({
    type: 'move_unit',
    unit_id: unitId,
    x: x,
    y: y,
    location: location
  }));
}

// Воспроизвести бой
function replayBattle(events) {
  events.forEach(event => {
    setTimeout(() => {
      switch(event.type) {
        case 'movement':
          moveUnitAnimation(event.unit_id, event.position);
          break;
        case 'attack':
          showAttackAnimation(event.unit_id, event.target_id, event.damage);
          break;
        case 'death':
          showDeathAnimation(event.unit_id);
          break;
      }
    }, event.time * 1000);
  });
}
```

---

## Обработка ошибок

WebSocket может закрыться по следующим причинам:

- `1000` - Нормальное закрытие
- `1001` - Клиент ушел
- `1008` - Policy violation (невалидный токен)
- `1011` - Server error

```javascript
ws.onclose = (event) => {
  console.log('Connection closed:', event.code, event.reason);
  
  if (event.code === 1008) {
    // Невалидный токен - нужен повторный логин
    redirectToLogin();
  } else {
    // Попытка переподключения
    setTimeout(() => reconnect(), 3000);
  }
};
```