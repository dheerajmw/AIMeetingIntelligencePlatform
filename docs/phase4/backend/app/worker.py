from __future__ import annotations

from redis import Redis
from rq import Worker

from .config import settings


def main() -> None:
    redis_conn = Redis.from_url(settings.redis_url)
    w = Worker([settings.rq_queue_name], connection=redis_conn)
    w.work(with_scheduler=False)


if __name__ == "__main__":
    main()

