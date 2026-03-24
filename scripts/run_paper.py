from __future__ import annotations

import time

from app.config.settings import get_settings
from app.core.service import build_bot_service
from app.exchange.simulated import SimulatedExchangeAdapter
from app.paper.job import PaperTradingJob
from app.strategies.registry import build_strategy
from app.utils.logging import configure_logging, get_logger


def main(steps: int = 20) -> None:
    configure_logging()
    logger = get_logger("paper_runner")
    settings = get_settings()
    exchange = SimulatedExchangeAdapter(symbol=settings.strategy.symbol)
    strategy = build_strategy(settings.strategy.name)
    service = build_bot_service(settings=settings, exchange=exchange, strategy=strategy)
    job = PaperTradingJob(service)
    logger.info("paper_job_start", steps=steps, strategy=strategy.name)
    for _ in range(steps):
        result = job.start(steps=1)[0]
        logger.info("paper_step", cash=result["cash"], equity=result["equity"], outcome=str(result["outcome"]))
        time.sleep(0.01)
    logger.info("paper_job_done", trades=len(service.execution.paper_broker.portfolio.trades))


if __name__ == "__main__":
    main()
