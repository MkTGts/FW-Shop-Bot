import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    bot_token: str
    admin_ids: List[int]

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("BOT_TOKEN", "")
        if not token:
            raise RuntimeError("Переменная окружения BOT_TOKEN не задана")

        raw_admins = os.getenv("ADMIN_IDS", "")
        admin_ids: List[int] = []
        for part in raw_admins.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                admin_ids.append(int(part))
            except ValueError:
                continue

        return cls(bot_token=token, admin_ids=admin_ids)


settings = Settings.from_env()
