from __future__ import annotations

from dataclasses import dataclass

from app.core.service import BotService
from app.exchange.simulated import SimulatedExchangeAdapter


@dataclass
class PaperTradingJob:
    service: BotService
    running: bool = False

    def start(self, steps: int = 1) -> list[dict]:
        self.running = True
        results: list[dict] = []
        for _ in range(steps):
            results.append(self.service.step())
            if isinstance(self.service.exchange, SimulatedExchangeAdapter):
                self.service.exchange.step()
        return results

    def stop(self) -> None:
        self.running = False
