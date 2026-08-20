"""Small user-facing commands for the fan-only service."""

import logging
import sys

from hhd.http.ctl import send_event

logger = logging.getLogger(__name__)


def main() -> None:
    """Request the fan overlay without requiring a controller/input plugin."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    try:
        response = send_event({"type": "special", "event": "overlay"})
        if response.status != 200:
            logger.error("Fan service rejected the overlay request (%s)", response.status)
            raise SystemExit(2)
    except FileNotFoundError:
        logger.error("Fan service is not running: /run/hhd/api was not found")
        raise SystemExit(1)
    except (ConnectionError, PermissionError, OSError) as error:
        logger.error("Could not contact the fan service: %s", error)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
