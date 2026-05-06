# Система боя

## Обзор

Бой симулируется на сервере с тиком 0,1 секунды. Все события записываются и отправляются клиенту для воспроизведения.

---

## Координатная система

### Размер поля

- **Ширина:** 7 клеток (X: 0-6)
- **Высота:** 8 клеток (Y: 0-7)
- **Всего:** 56 клеток

### Половины поля

```
Player 1: Y = 0-3 (4 ряда, 28 клеток)
Player 2: Y = 4-7 (4 ряда, 28 клеток)
```

### Центры клеток

**Важно:** Юниты размещаются в **центрах клеток**, а не в углах.

```
Клетка [0, 0]: центр = (0.5, 0.5)
Клетка [1, 0]: центр = (1.5, 0.5)
Клетка [2, 1]: центр = (2.5, 1.5)
Клетка [6, 7]: центр = (6.5, 7.5)
```

**Формула:**
```
position_x = grid_x + 0.5
position_y = grid_y + 0.5
```

**Обратное преобразование:**
```javascript
grid_x = Math.floor(position_x);  // 2.5 → 2
grid_y = Math.floor(position_y);  // 1.5 → 1
```

---

## Механика боя

### Симуляция

Бой симулируется с шагом **0.1 секунды** (100ms):

```
TICK 0: t=0.0s
TICK 1: t=0.1s
TICK 2: t=0.2s
...
TICK 50: t=5.0s
```

### FSM (Finite State Machine)

Каждый юнит имеет состояния:

1. **MOVING** - двигается к врагу
2. **ATTACKING** - атакует врага

### Алгоритм каждого тика

```
Для каждого юнита:
  1. Найти ближайшего врага
  2. Вычислить расстояние до врага (по клеткам)
  3. Если расстояние > радиус атаки:
     → ДВИГАТЬСЯ к врагу
  4. Если расстояние <= радиус атаки:
     а) Проверить стоит ли в центре клетки:
        - НЕТ → ДВИГАТЬСЯ к центру клетки
        - ДА → переход к б)
     б) Проверить кулдаун атаки:
        - НЕ ГОТОВ → ЖДАТЬ
        - ГОТОВ → АТАКОВАТЬ
```

---

## Движение

### Плавное движение

Юниты двигаются плавно:

```javascript
// Направление к цели
dx = target.position_x - unit.position_x;
dy = target.position_y - unit.position_y;
distance = Math.sqrt(dx*dx + dy*dy);

// Нормализация
dx_norm = dx / distance;
dy_norm = dy / distance;

// Движение
move_distance = unit.move_speed * 0.1;  // 0.1 сек
unit.position_x += dx_norm * move_distance;
unit.position_y += dy_norm * move_distance;
```

**Пример:**
```
Warrior (move_speed=2.0) за 0.1 сек двигается на 0.2 клетки
(2.5, 1.5) → (2.7, 1.7) → (2.9, 1.9) → (3.1, 2.1) → ...
```

### Выравнивание на клетку

Перед атакой юнит выравнивается на центр клетки:

```javascript
grid_x = Math.floor(unit.position_x);
grid_y = Math.floor(unit.position_y);

target_x = grid_x + 0.5;
target_y = grid_y + 0.5;

// Двигаться к (target_x, target_y)
```

---

## Атака

### Условия для атаки

Юнит может атаковать если **ВСЕ** условия выполнены:

1. ✅ Юнит жив (hp > 0)
2. ✅ Есть цель для атаки
3. ✅ Цель в радиусе атаки
4. ✅ Юнит стоит в центре клетки (X.5, Y.5)
5. ✅ Прошло откат кулдауна последней атаки

### Радиус атаки

Используется **Чебышевское расстояние** (8 направлений):

```javascript
grid_x1 = Math.floor(unit.position_x);
grid_y1 = Math.floor(unit.position_y);
grid_x2 = Math.floor(target.position_x);
grid_y2 = Math.floor(target.position_y);

distance = Math.max(
  Math.abs(grid_x2 - grid_x1),
  Math.abs(grid_y2 - grid_y1)
);

if (distance <= unit.range) {
  // Может атаковать
}
```

**Важно:** Расстояние считается между **клетками**, а не точными координатами

**Пример:**
```
Warrior на (2.5, 1.5) - клетка [2, 1]
Archer на (6.9, 1.3) - клетка [6, 1]

distance = max(|6-2|, |1-1|) = 4

Если радиус атаки = 4 → МОЖЕТ атаковать
Не важно что Archer на (6.9, 1.3) - он в клетке [6, 1]!
```

### Радиус атаки по типам

```
Warrior (melee): range = 1
  ■ ■ ■
  ■ W ■  ← Может атаковать 8 соседних клеток
  ■ ■ ■

Archer (ranged): range = 5
  ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■
  ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■
  ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■
  ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■
  ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■
  ■ ■ ■ ■ ■ A ■ ■ ■ ■ ■  ← Может атаковать большую область
  ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■
  ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■
  ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■
  ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■
  ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■

```

### Attack Speed

`attack_speed` = **время между атаками в секундах**

```javascript
// Может ли атаковать?
can_attack = (current_time - last_attack_time) >= attack_speed;

// Примеры:
attack_speed = 1.0  → атака каждую 1 секунду
attack_speed = 0.5  → атака каждые 0.5 сек (быстрее)
attack_speed = 1.5  → атака каждые 1.5 сек (медленнее)
```

### Урон

```javascript
damage = unit.attack;

// Крит
if (Math.random() < unit.crit_chance) {
  damage = Math.floor(damage * unit.crit_damage);
}

target.hp -= damage;
```

**Пример:**
```
Warrior: attack=20, crit_chance=0.0, crit_damage=2.0
  → Урон: 20 (без крита)

Archer: attack=15, crit_chance=0.2, crit_damage=2.0
  → Урон: 15 (80% шанс) или 30 (20% шанс крита)
```

### Одновременные атаки

Все атаки в одном тике происходят **одновременно**:

```
TICK 10:
  1. Warrior атакует Archer (урон 20)
  2. Archer атакует Warrior (урон 15)
  3. Урон применяется одновременно
  
Результат:
  Warrior: 100 - 15 = 85 HP
  Archer: 60 - 20 = 40 HP
```

Это важно для баланса! Если оба юнита убивают друг друга → ничья.

---

## Смерть юнита

Юнит умирает когда `hp <= 0`:

```javascript
if (unit.hp <= 0) {
  // Создать событие смерти
  events.push({
    time: current_time,
    type: "death",
    unit_id: unit.id
  });
  
  // Юнит больше не участвует в бою
}
```

---

## Условие окончания боя

Бой заканчивается когда **у одного игрока все юниты мертвы**:

```javascript
player1_alive = units.filter(u => u.owner === "player1" && u.hp > 0).length;
player2_alive = units.filter(u => u.owner === "player2" && u.hp > 0).length;

if (player1_alive === 0 || player2_alive === 0) {
  // Бой закончен
}
```

---

## События боя

### Типы событий

```typescript
type BattleEvent = 
  | { time: number, type: "battle_start" }
  | { time: number, type: "movement", unit_id: string, position: [number, number] }
  | { time: number, type: "attack", unit_id: string, target_id: string, damage: number, crit: boolean }
  | { time: number, type: "death", unit_id: string }
  | { time: number, type: "battle_end" };
```

### Воспроизведение на клиенте

```javascript
function replayBattle(events) {
  events.forEach(event => {
    setTimeout(() => {
      switch(event.type) {
        case 'battle_start':
          console.log('Battle started');
          break;
          
        case 'movement':
          // Плавно переместить юнита
          animateUnitMovement(event.unit_id, event.position);
          break;
          
        case 'attack':
          // Показать анимацию атаки
          showAttackAnimation(event.unit_id, event.target_id);
          // Показать урон
          showDamageNumber(event.target_id, event.damage, event.crit);
          break;
          
        case 'death':
          // Показать анимацию смерти
          showDeathAnimation(event.unit_id);
          break;
          
        case 'battle_end':
          console.log('Battle ended');
          break;
      }
    }, event.time * 1000);  // Время в миллисекундах
  });
}
```

---

## Характеристики юнитов

Все характеристики берутся из БД (таблица `unit_configs`):

```sql
SELECT * FROM unit_configs;
```

**Примерные значения:**

| Тип | HP | Attack | Attack Speed | Range | Move Speed | Cost |
|-----|-----|--------|--------------|-------|------------|------|
| Warrior | 100 | 20 | 1.0 | 1 | 2.0 | 3 |
| Archer | 60 | 15 | 1.5 | 5 | 2.5 | 4 |
| Mage | 50 | 30 | 0.8 | 6 | 2.0 | 5 |

**При мердже:**
```
HP = base_hp * 2^(level-1)
Attack = base_attack * 2^(level-1)

Warrior lvl 2: HP=200, Attack=40
Warrior lvl 3: HP=400, Attack=80
Warrior lvl 4: HP=800, Attack=160
```