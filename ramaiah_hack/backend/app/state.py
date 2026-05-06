from __future__ import annotations

from dataclasses import dataclass, field

from services.data_registry import DataRegistry
from simulation.replay_manager import ReplayManager


@dataclass
class AppState:
    data: DataRegistry = field(default_factory=DataRegistry)
    replay: ReplayManager = field(default_factory=ReplayManager)

    def load_on_startup(self) -> None:
        self.data.load_all_datasets()
        self.replay.bootstrap_from_registry(self.data)

    def reload_all(self) -> None:
        # Used after dataset uploads
        self.load_on_startup()

