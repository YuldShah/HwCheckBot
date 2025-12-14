# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HwCheckBot is a Telegram bot for managing homework/exam submissions and checking student results. Built with Python 3 and aiogram v3 (modern async Telegram bot framework), using PostgreSQL for persistence.

## Commands

### Running the Bot
```bash
python bot.py
```

### Dependencies
```bash
pip install -r requirements.txt
```

### Database Backup/Restore (Heroku)
```bash
./rdb.sh   # Linux/Mac
rdb.bat    # Windows
```

## Architecture

### Core Components

- **bot.py** - Main entry point: initializes logging, loads env, registers handlers, creates tables, starts polling
- **loader.py** - Initializes Bot, Dispatcher, and DatabaseManager instances
- **jobs.py** - Scheduled task processing

### Handler Structure (aiogram Router pattern)

```
handlers/
├── admins/          # Admin-only handlers (test creation, access control, results)
├── users/           # User handlers (test taking, archive, results viewing)
├── not_handled.py   # Catch-all for unrecognized commands
└── register.py      # Combines all routers into dispatcher
```

Each handler module exports a `Router()` with role-based filters applied globally.

### Database Layer

```
utils/db/
├── storage.py       # DatabaseManager class (query, fetchone, fetchall methods)
└── [feature].py     # Feature-specific DB operations
```

Tables: `users`, `folders`, `exams`, `submissions`, `channel`, `attachments`, `scheduled_tasks`

### FSM States

```
states/
├── adm_states.py    # Admin state groups (test creation, archive, settings)
└── usr_states.py    # User state groups (test taking, results viewing)
```

### Custom Filters

```
filters/
├── access_finder.py # IsAdmin, IsUser, IsSubscriber filters
├── custom.py        # CbData, CbDataStartsWith for callback queries
└── types_delta.py   # Type checking filters
```

### Keyboards

```
keyboards/
├── regular/         # Persistent bottom keyboards
└── inline/          # Per-message callback keyboards
```

### Configuration

- **data/config.py** - Bot token, admin IDs, DB URL, pagination constants
- **data/dict.py** - UI strings and button labels (Uzbek/English)

## Key Patterns

### Handler Registration
```python
admin = Router()
admin.message.filter(IsAdmin())
# Handlers registered via dp.include_routers() in register.py
```

### Database Access
```python
result = db.fetchone("SELECT * FROM users WHERE userid=%s", (user_id,))
db.query("UPDATE users SET allowed=%s WHERE userid=%s", (allowed, user_id))
```

### State Management
```python
@handler.message(SomeState.some_state)
async def process_state(message, state):
    data = await state.get_data()
    await state.update_data(key=value)
    await state.set_state(NextState.next_state)
```

### Message/Callback Filtering
```python
@handler.message(F.text == dict.menu_text)
@handler.callback_query(CbData("callback_data"))
```

## Important Notes

- Timezone: All datetime conversions use UTC+5 (Uzbekistan timezone)
- Question types: Type 0 = open-ended, Type MCQ[n] = multiple choice with n options
- User permissions stored in `allowed` field: -1/0/1/2 represent different access levels
- Deployment via Heroku (Procfile: `worker: python bot.py`)
