import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    bot_token: str
    admin_ids: List[int]
    payment_phone: str

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

        payment_phone = os.getenv("PAYMENT_PHONE", "+79001234567")

        return cls(bot_token=token, admin_ids=admin_ids, payment_phone=payment_phone)


settings = Settings.from_env()
