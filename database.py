import aiosqlite

DB_PATH = "exam_bot.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id   INTEGER UNIQUE NOT NULL,
                full_name     TEXT NOT NULL,
                phone         TEXT NOT NULL,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS exam_types (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                is_active   INTEGER DEFAULT 1,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS exam_dates (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_type_id     INTEGER NOT NULL,
                exam_date        TEXT NOT NULL,
                location         TEXT NOT NULL,
                available_seats  INTEGER NOT NULL,
                registered_count INTEGER DEFAULT 0,
                is_active        INTEGER DEFAULT 1,
                created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exam_type_id) REFERENCES exam_types(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS registrations (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                exam_type_id INTEGER NOT NULL,
                exam_date_id INTEGER NOT NULL,
                status       TEXT DEFAULT 'active',
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (exam_type_id) REFERENCES exam_types(id),
                FOREIGN KEY (exam_date_id) REFERENCES exam_dates(id),
                UNIQUE(user_id, exam_date_id)
            );
        """)
        await db.commit()


# ─── User functions ────────────────────────────────────────────────────────────

async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        return await cur.fetchone()


async def create_user(telegram_id: int, full_name: str, phone: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT OR IGNORE INTO users (telegram_id, full_name, phone) VALUES (?, ?, ?)",
                (telegram_id, full_name, phone)
            )
            await db.commit()
            return True
        except Exception:
            return False


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users ORDER BY registered_at DESC")
        return await cur.fetchall()


# ─── Exam Type functions ────────────────────────────────────────────────────────

async def add_exam_type(name: str, description: str = "") -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO exam_types (name, description) VALUES (?, ?)",
                (name, description)
            )
            await db.commit()
            return True
        except Exception:
            return False


async def get_exam_types(active_only: bool = True):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if active_only:
            cur = await db.execute("SELECT * FROM exam_types WHERE is_active = 1 ORDER BY name")
        else:
            cur = await db.execute("SELECT * FROM exam_types ORDER BY name")
        return await cur.fetchall()


async def get_exam_type(type_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM exam_types WHERE id = ?", (type_id,))
        return await cur.fetchone()


async def toggle_exam_type(type_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE exam_types SET is_active = CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id = ?",
            (type_id,)
        )
        await db.commit()


async def delete_exam_type(type_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM exam_types WHERE id = ?", (type_id,))
        await db.commit()


# ─── Exam Date functions ────────────────────────────────────────────────────────

async def add_exam_date(exam_type_id: int, exam_date: str, location: str, available_seats: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO exam_dates (exam_type_id, exam_date, location, available_seats) VALUES (?, ?, ?, ?)",
            (exam_type_id, exam_date, location, available_seats)
        )
        await db.commit()


async def get_exam_dates(exam_type_id: int, active_only: bool = True):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if active_only:
            cur = await db.execute(
                """SELECT ed.*, et.name AS type_name
                   FROM exam_dates ed
                   JOIN exam_types et ON ed.exam_type_id = et.id
                   WHERE ed.exam_type_id = ? AND ed.is_active = 1
                         AND ed.registered_count < ed.available_seats
                   ORDER BY ed.exam_date""",
                (exam_type_id,)
            )
        else:
            cur = await db.execute(
                """SELECT ed.*, et.name AS type_name
                   FROM exam_dates ed
                   JOIN exam_types et ON ed.exam_type_id = et.id
                   WHERE ed.exam_type_id = ?
                   ORDER BY ed.exam_date""",
                (exam_type_id,)
            )
        return await cur.fetchall()


async def get_all_exam_dates():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT ed.*, et.name AS type_name
               FROM exam_dates ed
               JOIN exam_types et ON ed.exam_type_id = et.id
               ORDER BY et.name, ed.exam_date"""
        )
        return await cur.fetchall()


async def get_exam_date(date_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT ed.*, et.name AS type_name
               FROM exam_dates ed
               JOIN exam_types et ON ed.exam_type_id = et.id
               WHERE ed.id = ?""",
            (date_id,)
        )
        return await cur.fetchone()


async def delete_exam_date(date_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM exam_dates WHERE id = ?", (date_id,))
        await db.commit()


# ─── Registration functions ─────────────────────────────────────────────────────

async def register_for_exam(user_id: int, exam_type_id: int, exam_date_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO registrations (user_id, exam_type_id, exam_date_id) VALUES (?, ?, ?)",
                (user_id, exam_type_id, exam_date_id)
            )
            await db.execute(
                "UPDATE exam_dates SET registered_count = registered_count + 1 WHERE id = ?",
                (exam_date_id,)
            )
            await db.commit()
            return True
        except Exception:
            return False


async def get_user_registrations(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT r.id, r.exam_date_id, et.name AS type_name,
                      ed.exam_date, ed.location
               FROM registrations r
               JOIN exam_types et ON r.exam_type_id = et.id
               JOIN exam_dates  ed ON r.exam_date_id = ed.id
               WHERE r.user_id = ? AND r.status = 'active'
               ORDER BY ed.exam_date""",
            (user_id,)
        )
        return await cur.fetchall()


async def cancel_registration(registration_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT exam_date_id FROM registrations WHERE id = ? AND user_id = ? AND status='active'",
            (registration_id, user_id)
        )
        row = await cur.fetchone()
        if not row:
            return False
        await db.execute(
            "UPDATE registrations SET status = 'cancelled' WHERE id = ?",
            (registration_id,)
        )
        await db.execute(
            "UPDATE exam_dates SET registered_count = MAX(0, registered_count - 1) WHERE id = ?",
            (row[0],)
        )
        await db.commit()
        return True


async def check_already_registered(user_id: int, exam_date_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM registrations WHERE user_id=? AND exam_date_id=? AND status='active'",
            (user_id, exam_date_id)
        )
        return await cur.fetchone() is not None


# ─── Admin stats ────────────────────────────────────────────────────────────────

async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        users  = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        regs   = (await (await db.execute("SELECT COUNT(*) FROM registrations WHERE status='active'")).fetchone())[0]
        types  = (await (await db.execute("SELECT COUNT(*) FROM exam_types WHERE is_active=1")).fetchone())[0]
        dates  = (await (await db.execute("SELECT COUNT(*) FROM exam_dates WHERE is_active=1")).fetchone())[0]
        return {"users": users, "registrations": regs, "exam_types": types, "exam_dates": dates}


async def get_all_registrations():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT r.id, u.full_name, u.phone, et.name AS type_name,
                      ed.exam_date, ed.location, r.registered_at
               FROM registrations r
               JOIN users      u  ON r.user_id      = u.id
               JOIN exam_types et ON r.exam_type_id  = et.id
               JOIN exam_dates ed ON r.exam_date_id  = ed.id
               WHERE r.status = 'active'
               ORDER BY ed.exam_date, r.registered_at"""
        )
        return await cur.fetchall()


async def get_registrations_by_type(exam_type_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT r.id, u.full_name, u.phone, et.name AS type_name,
                      ed.exam_date, ed.location, r.registered_at
               FROM registrations r
               JOIN users      u  ON r.user_id      = u.id
               JOIN exam_types et ON r.exam_type_id  = et.id
               JOIN exam_dates ed ON r.exam_date_id  = ed.id
               WHERE r.exam_type_id = ? AND r.status = 'active'
               ORDER BY ed.exam_date, r.registered_at""",
            (exam_type_id,)
        )
        return await cur.fetchall()
