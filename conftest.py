import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("ADMIN_ID", "00000000-0000-0000-0000-000000000001")
os.environ.setdefault("ADMIN_NAME", "Admin")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_CREDS", "100.0")
os.environ.setdefault("ADMIN_PASSWORD", "AdminPass123!")
