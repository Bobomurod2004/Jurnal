#!/usr/bin/env python3
"""Reconcile activity_events so downloads never exceed views.

Historical (legacy) data was imported straight from ``publications.stat_views``
and ``publications.stat_alt``. Those legacy counters were never bot-filtered and
counted direct downloads that bypassed the article page, so the aggregate
``download`` total can sit above the ``view`` total — which is impossible for a
real reader (a download always implies a view).

This script trims the excess ``download`` events, preferring the unattributed
legacy rows (``publication_id IS NULL`` in the other/unknown country buckets)
that hold the bot inflation, so attributed per-country downloads are preserved.

Usage:
    python3 scripts/fix_activity_stats.py            # dry-run (no changes)
    python3 scripts/fix_activity_stats.py --apply     # apply the correction
    python3 scripts/fix_activity_stats.py --apply --cap-publications
                                                      # also cap publications.stat_alt <= stat_views

DB connection is taken from the same env vars the app uses:
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
"""

import argparse
import os
import sys

import psycopg2

LEGACY_BUCKETS = ('other', 'unknown', '')


def _connect():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', ''),
        dbname=os.getenv('DB_NAME', 'journal'),
    )


def _totals(cur):
    cur.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN event_type = 'download' THEN 1 ELSE 0 END), 0)
        FROM activity_events
        """
    )
    views, downloads = cur.fetchone()
    return int(views or 0), int(downloads or 0)


def _delete_download_rows(cur, count, legacy_only):
    """Delete up to ``count`` download rows, oldest first; returns rows deleted."""
    if count <= 0:
        return 0
    where_extra = ""
    if legacy_only:
        where_extra = (
            "AND publication_id IS NULL "
            "AND lower(COALESCE(country_key, '')) IN %(buckets)s"
        )
    cur.execute(
        f"""
        DELETE FROM activity_events
        WHERE ctid IN (
            SELECT ctid FROM activity_events
            WHERE event_type = 'download'
            {where_extra}
            ORDER BY created_at ASC, ctid ASC
            LIMIT %(limit)s
        )
        """,
        {'limit': count, 'buckets': LEGACY_BUCKETS},
    )
    return cur.rowcount


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Commit changes (default: dry-run)')
    parser.add_argument(
        '--cap-publications',
        action='store_true',
        help='Also clamp publications.stat_alt to publications.stat_views',
    )
    args = parser.parse_args()

    conn = _connect()
    conn.autocommit = False
    cur = conn.cursor()

    # Guard: table must exist.
    cur.execute("SELECT to_regclass('public.activity_events');")
    if not (cur.fetchone() or [None])[0]:
        print('activity_events table does not exist — nothing to do.')
        return 0

    views, downloads = _totals(cur)
    print(f'Before:  views={views:,}  downloads={downloads:,}')

    excess = downloads - views
    deleted = 0
    if excess > 0:
        print(f'Downloads exceed views by {excess:,} — trimming excess download events.')
        # Prefer legacy unattributed rows (bot inflation), then any download rows.
        deleted += _delete_download_rows(cur, excess, legacy_only=True)
        still = excess - deleted
        if still > 0:
            deleted += _delete_download_rows(cur, still, legacy_only=False)
        print(f'Deleted {deleted:,} download events.')
    else:
        print('Downloads already <= views — no event trimming needed.')

    capped_pubs = 0
    if args.cap_publications:
        cur.execute(
            """
            UPDATE publications
            SET stat_alt = stat_views
            WHERE COALESCE(stat_alt, 0) > COALESCE(stat_views, 0)
            """
        )
        capped_pubs = cur.rowcount
        print(f'Capped publications.stat_alt for {capped_pubs:,} rows.')

    new_views, new_downloads = _totals(cur)
    print(f'After:   views={new_views:,}  downloads={new_downloads:,}')

    if args.apply:
        conn.commit()
        print('APPLIED: changes committed.')
    else:
        conn.rollback()
        print('DRY-RUN: no changes committed. Re-run with --apply to commit.')

    cur.close()
    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
