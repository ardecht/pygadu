import sqlite3


class Database:
    def __init__(self):
        self.db = sqlite3.connect("database.db")
        self._prepare_database()

    def __del__(self):
        self.db.close()

    def _is_table_exists(self, table_name):
        result = self.db.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = (?)",
                                 [table_name]).fetchone()
        return result is not None

    def _prepare_database(self):
        if not self._is_table_exists("users"):
            self.db.execute("""
            CREATE TABLE "users" (
                "id"	INTEGER UNIQUE,
                "uin"	INTEGER NOT NULL UNIQUE,
                "password"	TEXT NOT NULL,
                "status"	INTEGER NOT NULL,
                "description"	TEXT,
                PRIMARY KEY("id")
            )
            """)
            self.db.commit()

    def find_user(self, uin):
        return self.db.execute("SELECT * FROM users WHERE uin = (?) LIMIT 1", [uin]).fetchone()

    def update_user_status(self, uin, status, description):
        self.db.execute("UPDATE users SET status = (?), description = (?) WHERE uin = (?)", [status, description, uin])
        self.db.commit()

    def find_and_delete_user_queued_messages(self, uin):
        messages = self.db.execute("SELECT * FROM messages WHERE recipient = (?)", [uin]).fetchall()
        self.db.execute("DELETE FROM messages WHERE recipient = (?)", [uin])
        self.db.commit()
        return messages

    def add_user_message_to_queue(self, sender, recipient, message):
        self.db.execute("INSERT INTO messages(sender, recipient, message) VALUES ((?), (?), (?))", [sender, recipient, message])
        self.db.commit()
        pass
