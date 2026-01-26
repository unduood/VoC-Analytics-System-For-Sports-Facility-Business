"""
One-time script to fix Facebook comment timestamps

Problem:
- Facebook webhook sends `created_time` as Unix timestamp (UTC)
- Old code used `datetime.fromtimestamp()` which converts to LOCAL timezone
- Server was running in Thailand (UTC+7), so times were stored 7 hours ahead
- Example: UTC 04:12:48 was stored as 11:12:48 (local time) without timezone info

Fix:
- Subtract 7 hours from stored times to get correct UTC
- Update both raw_data.created_time and created_at_source

Usage:
    docker-compose exec backend python scripts/fix_facebook_timestamps.py

    Or with dry-run (preview changes without saving):
    docker-compose exec backend python scripts/fix_facebook_timestamps.py --dry-run
"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone

# Add parent directory to path for imports
sys.path.insert(0, '/app')

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.feedback import FeedbackRecord


# Thailand timezone offset (UTC+7)
THAILAND_OFFSET_HOURS = 7


async def fix_facebook_timestamps(dry_run: bool = False):
    """Fix Facebook comment timestamps that were stored in local time"""

    print("=" * 60)
    print("Facebook Timestamp Fix Script")
    print("=" * 60)
    print(f"Mode: {'DRY RUN (no changes will be saved)' if dry_run else 'LIVE (changes will be saved)'}")
    print()

    async with AsyncSessionLocal() as db:
        # Find all Facebook records
        stmt = select(FeedbackRecord).where(
            FeedbackRecord.source_type == "facebook"
        )
        result = await db.execute(stmt)
        records = result.scalars().all()

        print(f"Found {len(records)} Facebook records")
        print()

        fixed_count = 0
        skipped_count = 0
        error_count = 0

        for record in records:
            try:
                raw_data = record.raw_data or {}
                created_time_str = raw_data.get("created_time")

                if not created_time_str:
                    print(f"  SKIP {record.id}: No created_time in raw_data")
                    skipped_count += 1
                    continue

                # Check if already has timezone info
                if "+" in created_time_str or created_time_str.endswith("Z"):
                    print(f"  SKIP {record.id}: Already has timezone ({created_time_str})")
                    skipped_count += 1
                    continue

                # Parse the naive datetime
                try:
                    naive_dt = datetime.fromisoformat(created_time_str)
                except ValueError:
                    print(f"  ERROR {record.id}: Cannot parse '{created_time_str}'")
                    error_count += 1
                    continue

                # The stored time is local Thailand time (UTC+7)
                # To get UTC, subtract 7 hours
                correct_utc = naive_dt - timedelta(hours=THAILAND_OFFSET_HOURS)
                correct_utc = correct_utc.replace(tzinfo=timezone.utc)
                correct_utc_iso = correct_utc.isoformat()

                # Show the fix
                print(f"  FIX {record.id}:")
                print(f"      created_time: {created_time_str} -> {correct_utc_iso}")
                print(f"      created_at_source: {record.created_at_source} -> {correct_utc}")

                if not dry_run:
                    # Update raw_data.created_time
                    updated_raw_data = {**raw_data, "created_time": correct_utc_iso}

                    # Update the record
                    record.raw_data = updated_raw_data
                    record.created_at_source = correct_utc

                fixed_count += 1

            except Exception as e:
                print(f"  ERROR {record.id}: {e}")
                error_count += 1

        if not dry_run and fixed_count > 0:
            await db.commit()
            print()
            print("Changes committed to database.")

        print()
        print("=" * 60)
        print("Summary:")
        print(f"  Fixed:   {fixed_count}")
        print(f"  Skipped: {skipped_count}")
        print(f"  Errors:  {error_count}")
        print("=" * 60)

        if dry_run and fixed_count > 0:
            print()
            print("This was a dry run. Run without --dry-run to apply changes.")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    asyncio.run(fix_facebook_timestamps(dry_run=dry_run))
