import os 
import logging 
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def write_to_silver(df, source: str ="offres", mode: str = "overwrite") -> str:
    """
    Writes a transformed DataFrame to the Silver layer in Delta format.

    Args:
        df:     The validated Silver DataFrame to write
        source: Logical name for this Silver table (e.g. "offres")
        mode:   Write mode ("overwrite" or "append")

    Returns:
        The full path written to (for logging/tracking purposes)
    """

    bukcet = os.getenv("MINIO_BUCKET")
    path = f"s3a://{bukcet}/silver/{source}"

    (
        df.write
        .format("delta")
        .mode(mode)
        .save(path)
    )

    logger.info("Silver data written to %s (mode=%s)", path, mode)
    return path