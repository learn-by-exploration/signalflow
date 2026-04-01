# mkg/domain/services/retention_policy.py
"""RetentionPolicy — configurable data retention periods.

Ensures compliance with data retention requirements:
- SEBI IA Regulations 2013 require audit records for minimum 5 years
- Articles kept for 90 days (configurable)
- Entity data kept for 1 year (configurable)

This service determines whether records have expired and provides
expiry dates for purging operations.
"""

import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class RetentionPolicy:
    """Configurable data retention policy.

    Default retention periods:
    - Articles: 90 days
    - Entities: 365 days (1 year)
    - Audit records: 1825 days (5 years, SEBI IA Regulations 2013 requirement)
    """

    def __init__(
        self,
        article_retention_days: int = 90,
        entity_retention_days: int = 365,
        audit_retention_days: int = 1825,
    ) -> None:
        self.article_retention_days = article_retention_days
        self.entity_retention_days = entity_retention_days
        self.audit_retention_days = audit_retention_days

        self._retention_map = {
            "article": article_retention_days,
            "entity": entity_retention_days,
            "audit": audit_retention_days,
        }

    def is_expired(self, data_type: str, created_at: datetime) -> bool:
        """Check if a record has exceeded its retention period.

        Args:
            data_type: One of "article", "entity", "audit".
            created_at: When the record was created (must be timezone-aware).

        Returns:
            True if the record is expired, False otherwise.
            Unknown data types never expire (safety default).
        """
        retention_days = self._retention_map.get(data_type)
        if retention_days is None:
            return False

        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        return created_at < cutoff

    def get_expiry_date(self, data_type: str) -> datetime:
        """Get the cutoff date for a given data type.

        Records created before this date are considered expired.

        Args:
            data_type: One of "article", "entity", "audit".

        Returns:
            Cutoff datetime. Records older than this should be purged.
        """
        retention_days = self._retention_map.get(data_type, 365)
        return datetime.now(timezone.utc) - timedelta(days=retention_days)
