import btconfig
from .simple_strategy import SimpleStrategy  # noqa: *


res = btconfig.run(btconfig.MODE_BACKTEST, "config.yaml")
