import psycopg2


class Database:

    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            database="Kanban",
            user="postgres",
            password="#Gabriel19",
            port="5432"
        )
        self.cursor = self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()