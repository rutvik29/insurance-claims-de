"""Data loading utilities for writing DataFrames to SQLite via SQLAlchemy."""

import logging
import time
from typing import Optional

import pandas as pd
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class DataLoader:
    """Load DataFrames into SQLite using chunked writes."""

    def __init__(self, engine: Engine, chunk_size: int = 1000) -> None:
        self.engine = engine
        self.chunk_size = chunk_size

    def load_table(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: str = "replace",
    ) -> int:
        """
        Write a DataFrame to a SQLite table in chunks.

        Args:
            df:         DataFrame to load.
            table_name: Target table name.
            if_exists:  pandas behaviour ('replace', 'append', 'fail').

        Returns:
            Number of rows written.
        """
        if df.empty:
            logger.warning("DataFrame for table '%s' is empty; skipping load.", table_name)
            return 0

        start = time.time()
        total_rows = len(df)
        logger.info("Loading '%s': %d rows in chunks of %d ...", table_name, total_rows, self.chunk_size)

        chunks = [df.iloc[i : i + self.chunk_size] for i in range(0, total_rows, self.chunk_size)]
        written = 0
        for idx, chunk in enumerate(chunks):
            exists = if_exists if idx == 0 else "append"
            chunk.to_sql(table_name, con=self.engine, if_exists=exists, index=False)
            written += len(chunk)

        elapsed = time.time() - start
        logger.info(
            "Loaded '%s': %d rows in %.2f s (%.0f rows/s)",
            table_name,
            written,
            elapsed,
            written / max(elapsed, 0.001),
        )
        return written

    def load_all(self, tables: dict) -> dict:
        """
        Load multiple tables.

        Args:
            tables: Mapping of table_name -> DataFrame.

        Returns:
            Mapping of table_name -> rows_written.
        """
        results = {}
        for table_name, df in tables.items():
            results[table_name] = self.load_table(df, table_name)
        return results
