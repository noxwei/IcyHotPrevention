"""Abstract base pipeline for data ingestion with checkpoint/resume support."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Generic, Optional, TypeVar
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

T = TypeVar("T")  # Record type
C = TypeVar("C")  # Checkpoint type


@dataclass
class PipelineCheckpoint:
    """Checkpoint state for pipeline resumption."""

    cursor: Any = None
    page: int = 0
    offset: int = 0
    last_id: Optional[str] = None
    last_date: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class PipelineStats:
    """Statistics for a pipeline run."""

    records_fetched: int = 0
    records_transformed: int = 0
    records_upserted: int = 0
    records_skipped: int = 0
    errors: int = 0
    batches_processed: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_error: Optional[str] = None

    @property
    def duration_seconds(self) -> float:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0


class BasePipeline(ABC, Generic[T, C]):
    """Abstract base class for data ingestion pipelines.

    Subclasses must implement:
        - pipeline_name: Unique identifier for the pipeline
        - fetch_batch: Fetch a batch of records from the source
        - transform: Transform a raw record to the target format
        - upsert: Insert or update records in the database

    Features:
        - Checkpoint-based resumption
        - Configurable batch sizes
        - Stats tracking
        - Dry-run mode
        - Max batches limit

    Usage:
        class MyPipeline(BasePipeline[MyRecord, str]):
            pipeline_name = "my_source"

            async def fetch_batch(self, checkpoint):
                ...

            async def transform(self, record):
                ...

            async def upsert(self, records):
                ...

        pipeline = MyPipeline(session)
        stats = await pipeline.run(max_batches=10)
    """

    pipeline_name: str = "base"
    default_batch_size: int = 100

    def __init__(
        self,
        session: AsyncSession,
        batch_size: Optional[int] = None,
    ):
        self.session = session
        self.batch_size = batch_size or self.default_batch_size
        self._stats = PipelineStats()

    @property
    def stats(self) -> PipelineStats:
        """Current pipeline statistics."""
        return self._stats

    async def get_checkpoint(self) -> PipelineCheckpoint:
        """Load checkpoint from database.

        Returns:
            PipelineCheckpoint with saved state or defaults
        """
        sql = text("""
            SELECT checkpoint, records_processed, last_error, last_error_at
            FROM integration.sync_state
            WHERE pipeline_name = :name
        """)

        result = await self.session.execute(sql, {"name": self.pipeline_name})
        row = result.fetchone()

        if row is None:
            return PipelineCheckpoint()

        checkpoint_data = row.checkpoint or {}
        return PipelineCheckpoint(
            cursor=checkpoint_data.get("cursor"),
            page=checkpoint_data.get("page", 0),
            offset=checkpoint_data.get("offset", 0),
            last_id=checkpoint_data.get("last_id"),
            last_date=checkpoint_data.get("last_date"),
            metadata=checkpoint_data.get("metadata", {}),
        )

    async def save_checkpoint(
        self,
        checkpoint: PipelineCheckpoint,
        status: str = "running",
        error: Optional[str] = None,
    ) -> None:
        """Save checkpoint to database.

        Args:
            checkpoint: Checkpoint state to save
            status: Pipeline status (idle, running, error, completed)
            error: Error message if any
        """
        checkpoint_data = {
            "cursor": checkpoint.cursor,
            "page": checkpoint.page,
            "offset": checkpoint.offset,
            "last_id": checkpoint.last_id,
            "last_date": (
                checkpoint.last_date.isoformat() if checkpoint.last_date else None
            ),
            "metadata": checkpoint.metadata,
        }

        sql = text("""
            INSERT INTO integration.sync_state
                (pipeline_name, checkpoint, records_processed, status,
                 last_error, last_error_at, last_sync_at, updated_at)
            VALUES
                (:name, :checkpoint, :records, :status,
                 :error, :error_at, NOW(), NOW())
            ON CONFLICT (pipeline_name) DO UPDATE SET
                checkpoint = :checkpoint,
                records_processed = sync_state.records_processed + :records,
                status = :status,
                last_error = COALESCE(:error, sync_state.last_error),
                last_error_at = COALESCE(:error_at, sync_state.last_error_at),
                last_sync_at = NOW(),
                updated_at = NOW()
        """)

        await self.session.execute(
            sql,
            {
                "name": self.pipeline_name,
                "checkpoint": checkpoint_data,
                "records": self._stats.records_upserted,
                "status": status,
                "error": error,
                "error_at": datetime.now(timezone.utc) if error else None,
            },
        )
        await self.session.commit()

    @abstractmethod
    async def fetch_batch(
        self, checkpoint: PipelineCheckpoint
    ) -> tuple[list[T], PipelineCheckpoint]:
        """Fetch a batch of records from the source.

        Args:
            checkpoint: Current checkpoint state

        Returns:
            Tuple of (records, new_checkpoint)
            Empty records list signals end of data
        """
        raise NotImplementedError

    @abstractmethod
    async def transform(self, record: T) -> Optional[dict]:
        """Transform a raw record to the target format.

        Args:
            record: Raw record from source

        Returns:
            Transformed record dict or None to skip
        """
        raise NotImplementedError

    @abstractmethod
    async def upsert(self, records: list[dict]) -> int:
        """Insert or update records in the database.

        Args:
            records: Transformed records to upsert

        Returns:
            Number of records affected
        """
        raise NotImplementedError

    async def run(
        self,
        max_batches: Optional[int] = None,
        dry_run: bool = False,
        reset_checkpoint: bool = False,
    ) -> PipelineStats:
        """Run the pipeline.

        Args:
            max_batches: Maximum number of batches to process (None = unlimited)
            dry_run: If True, don't write to database
            reset_checkpoint: If True, start from beginning

        Returns:
            PipelineStats with run results
        """
        self._stats = PipelineStats(started_at=datetime.now(timezone.utc))

        # Get or reset checkpoint
        if reset_checkpoint:
            checkpoint = PipelineCheckpoint()
        else:
            checkpoint = await self.get_checkpoint()

        logger.info(
            f"Starting pipeline '{self.pipeline_name}' "
            f"(batch_size={self.batch_size}, dry_run={dry_run})"
        )

        batch_count = 0
        try:
            while True:
                # Check batch limit
                if max_batches is not None and batch_count >= max_batches:
                    logger.info(f"Reached max batches limit ({max_batches})")
                    break

                # Fetch batch
                records, new_checkpoint = await self.fetch_batch(checkpoint)
                self._stats.records_fetched += len(records)

                if not records:
                    logger.info("No more records to fetch")
                    break

                # Transform records
                transformed = []
                for record in records:
                    try:
                        result = await self.transform(record)
                        if result is not None:
                            transformed.append(result)
                            self._stats.records_transformed += 1
                        else:
                            self._stats.records_skipped += 1
                    except Exception as e:
                        logger.error(f"Transform error: {e}")
                        self._stats.errors += 1

                # Upsert if not dry run
                if transformed and not dry_run:
                    try:
                        affected = await self.upsert(transformed)
                        self._stats.records_upserted += affected
                    except Exception as e:
                        logger.error(f"Upsert error: {e}")
                        self._stats.errors += 1
                        self._stats.last_error = str(e)
                        await self.save_checkpoint(
                            checkpoint, status="error", error=str(e)
                        )
                        raise

                # Update checkpoint
                checkpoint = new_checkpoint
                batch_count += 1
                self._stats.batches_processed = batch_count

                # Save checkpoint periodically
                if batch_count % 10 == 0 and not dry_run:
                    await self.save_checkpoint(checkpoint, status="running")

                logger.debug(
                    f"Batch {batch_count}: fetched={len(records)}, "
                    f"transformed={len(transformed)}"
                )

            # Final checkpoint save
            self._stats.completed_at = datetime.now(timezone.utc)
            if not dry_run:
                await self.save_checkpoint(checkpoint, status="completed")

            logger.info(
                f"Pipeline '{self.pipeline_name}' completed: "
                f"batches={self._stats.batches_processed}, "
                f"records={self._stats.records_upserted}"
            )

        except Exception as e:
            self._stats.completed_at = datetime.now(timezone.utc)
            self._stats.last_error = str(e)
            logger.error(f"Pipeline '{self.pipeline_name}' failed: {e}")
            raise

        return self._stats
