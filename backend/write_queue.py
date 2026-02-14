"""
Async log writer queue for high-performance log ingestion.

This module implements a background worker that:
1. Accepts log entries via a non-blocking queue
2. Batches logs together (configurable batch size)
3. Writes batches to database in a single transaction
4. Flushes periodically to ensure bounded latency

Performance characteristics:
- Non-blocking ingestion (returns immediately)
- Batch writes (100-1000x faster than individual inserts)
- Bounded latency (flushes every flush_interval seconds)
- Handles bursts (queue buffers up to maxsize logs)

Configuration:
- batch_size: Number of logs to batch before writing (default: 100)
- flush_interval: Max seconds between flushes (default: 0.1s = 100ms)
- queue_maxsize: Max logs in queue before blocking (default: 10000)
"""

import queue
import threading
import time
import logging
from typing import Dict, Any, Optional
from database import create_logs_bulk

logger = logging.getLogger(__name__)


class LogWriteQueue:
    """
    Background log writer with batching and periodic flushing.
    """

    def __init__(
        self,
        batch_size: int = 100,
        flush_interval: float = 0.1,
        queue_maxsize: int = 10000,
    ):
        """
        Initialize the write queue.

        Args:
            batch_size: Number of logs to batch before writing
            flush_interval: Max seconds between flushes (for latency bounds)
            queue_maxsize: Max queue capacity (prevents memory exhaustion)
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue = queue.Queue(maxsize=queue_maxsize)
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None

        # Statistics
        self.total_enqueued = 0
        self.total_written = 0
        self.total_dropped = 0
        self.total_errors = 0

    def start(self):
        """Start the background writer thread."""
        if self.running:
            logger.warning("Write queue already running")
            return

        self.running = True
        self.worker_thread = threading.Thread(
            target=self._writer_loop, daemon=True, name="LogWriterThread"
        )
        self.worker_thread.start()
        logger.info(
            f"Log write queue started: batch_size={self.batch_size}, "
            f"flush_interval={self.flush_interval}s, "
            f"queue_maxsize={self.queue.maxsize}"
        )

    def stop(self, timeout: float = 5.0):
        """
        Stop the writer and flush remaining logs.

        Args:
            timeout: Max seconds to wait for graceful shutdown
        """
        if not self.running:
            return

        logger.info("Stopping write queue...")
        self.running = False

        if self.worker_thread:
            self.worker_thread.join(timeout=timeout)
            if self.worker_thread.is_alive():
                logger.warning("Write queue did not stop gracefully")
            else:
                logger.info("Write queue stopped cleanly")

    def enqueue(self, log: Dict[str, Any]) -> bool:
        """
        Add log to write queue (non-blocking).

        Args:
            log: Log dictionary with keys: app_id, level, message,
                 structured_data, tags, timestamp

        Returns:
            True if enqueued successfully, False if queue is full
        """
        try:
            self.queue.put_nowait(log)
            self.total_enqueued += 1
            return True
        except queue.Full:
            self.total_dropped += 1
            logger.error(
                f"Write queue full (size={self.queue.qsize()}), dropping log. "
                f"Total dropped: {self.total_dropped}"
            )
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            "queue_size": self.queue.qsize(),
            "queue_capacity": self.queue.maxsize,
            "total_enqueued": self.total_enqueued,
            "total_written": self.total_written,
            "total_dropped": self.total_dropped,
            "total_errors": self.total_errors,
            "is_running": self.running,
        }

    def _writer_loop(self):
        """
        Background thread that writes batches.

        Algorithm:
        1. Collect logs into buffer
        2. Flush when: batch full OR time elapsed OR shutting down
        3. Write batch to DB using bulk insert
        4. Handle errors gracefully (log and continue)
        """
        buffer = []
        last_flush = time.time()

        while self.running or not self.queue.empty():
            try:
                # Calculate timeout: flush when time elapsed
                time_since_flush = time.time() - last_flush
                timeout = max(0.01, self.flush_interval - time_since_flush)

                # Try to get a log (blocking with timeout)
                try:
                    log = self.queue.get(timeout=timeout)
                    buffer.append(log)
                except queue.Empty:
                    # Timeout reached, flush if we have data
                    pass

                # Determine if we should flush
                should_flush = (
                    len(buffer) >= self.batch_size  # Batch is full
                    or (time.time() - last_flush) >= self.flush_interval  # Time elapsed
                    or (not self.running and buffer)  # Shutting down with pending data
                )

                if should_flush and buffer:
                    self._flush_buffer(buffer)
                    buffer = []
                    last_flush = time.time()

            except Exception as e:
                logger.error(f"Unexpected error in writer loop: {e}", exc_info=True)
                self.total_errors += 1
                # Clear buffer to prevent infinite error loop
                buffer = []
                time.sleep(0.1)

        # Final flush on shutdown
        if buffer:
            logger.info(f"Final flush: {len(buffer)} logs")
            self._flush_buffer(buffer)

    def _flush_buffer(self, buffer: list):
        """
        Write a buffer of logs to the database.

        Args:
            buffer: List of log dictionaries to write
        """
        if not buffer:
            return

        try:
            start_time = time.time()
            log_ids = create_logs_bulk(buffer)
            elapsed = time.time() - start_time

            self.total_written += len(buffer)

            # Log performance metrics periodically
            if self.total_written % 1000 < len(buffer):
                throughput = len(buffer) / elapsed if elapsed > 0 else 0
                logger.info(
                    f"Wrote {len(buffer)} logs in {elapsed * 1000:.1f}ms "
                    f"({throughput:.0f} logs/sec). Total written: {self.total_written}"
                )
            else:
                logger.debug(f"Wrote {len(buffer)} logs in {elapsed * 1000:.1f}ms")

        except Exception as e:
            self.total_errors += 1
            logger.error(
                f"Failed to write batch of {len(buffer)} logs: {e}", exc_info=True
            )
            # Note: We drop the failed batch to avoid blocking the queue
            # In production, you might want to write to a dead-letter queue


# Global singleton instance
_log_writer: Optional[LogWriteQueue] = None


def get_log_writer(
    batch_size: int = 100, flush_interval: float = 0.1, queue_maxsize: int = 10000
) -> LogWriteQueue:
    """
    Get or create the global log writer instance.

    Args:
        batch_size: Number of logs per batch
        flush_interval: Max seconds between flushes
        queue_maxsize: Max queue size

    Returns:
        LogWriteQueue instance
    """
    global _log_writer
    if _log_writer is None:
        _log_writer = LogWriteQueue(
            batch_size=batch_size,
            flush_interval=flush_interval,
            queue_maxsize=queue_maxsize,
        )
    return _log_writer
