import sqlite3
c = sqlite3.connect("healthtag.db")
c.execute("DELETE FROM messages WHERE kind='contact'")
c.commit()