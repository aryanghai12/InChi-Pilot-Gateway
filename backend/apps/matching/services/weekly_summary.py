"""
Weekly Matching Summary (C7 weekly reporting).

Aggregates match-run records by PROGRAMME WEEK — the same weekly period used by
the team's weekly reports (docs/daily-reports/README.md). There is deliberately
no daily aggregation.

Programme weeks are 7-day windows starting Monday 26 October 2026, the proposed
revised timeline in MVP_FEATURES §13 (pending D-19). The start date is a
parameter so the summary follows D-19 if the dates change.

Input is any iterable of result_handler.MatchRunRecord (or objects with the same
attributes), e.g. records rebuilt from Vishal's stored runs once they exist.
This module performs no database query and does not touch the dashboard (M9,
owned by Vishal/Abhishek).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component A (Django Integration Layer)
Status: Implemented.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, tzinfo

from django.utils import timezone

# Proposed revised timeline, MVP_FEATURES §13 — pending D-19.
PROGRAMME_START = date(2026, 10, 26)


@dataclass
class WeeklyMatchingSummary:
    week_number: int
    week_start: date
    week_end: date
    runs_total: int = 0
    runs_completed: int = 0
    runs_failed: int = 0
    runs_with_unapproved_config: int = 0
    candidates_submitted: int = 0
    candidates_ranked: int = 0
    candidates_excluded: int = 0
    candidates_insufficient_data: int = 0
    failure_codes: Counter = field(default_factory=Counter)
    requirements: set = field(default_factory=set)

    @property
    def requirements_matched(self) -> int:
        return len(self.requirements)

    def to_report_lines(self) -> list[str]:
        """Plain lines suitable for the weekly report's tests/validation section."""
        lines = [
            (
                f"Week {self.week_number} ({self.week_start:%d %b}–{self.week_end:%d %b %Y}): "
                f"{self.runs_total} match run(s) — {self.runs_completed} completed, {self.runs_failed} failed; "
                f"{self.requirements_matched} requirement(s)."
            ),
            (
                f"Candidates: {self.candidates_submitted} submitted, {self.candidates_ranked} ranked, "
                f"{self.candidates_excluded} excluded, {self.candidates_insufficient_data} insufficient data."
            ),
        ]
        if self.failure_codes:
            codes = ", ".join(f"{code} ×{count}" for code, count in sorted(self.failure_codes.items()))
            lines.append(f"Failures by code: {codes}.")
        if self.runs_with_unapproved_config:
            lines.append(f"{self.runs_with_unapproved_config} run(s) used an UNAPPROVED scoring configuration.")
        return lines


def programme_week(day: date, programme_start: date = PROGRAMME_START) -> int:
    """1-based programme week number; days before the start give 0 or negative weeks."""
    return (day - programme_start).days // 7 + 1


def _local_date(moment: datetime, tz: tzinfo | None) -> date:
    """Calendar date of a timestamp in the reporting timezone (aware) or as-is (naive)."""
    if timezone.is_aware(moment):
        return timezone.localtime(moment, tz or timezone.get_current_timezone()).date()
    return moment.date()


def summarise_weekly(
    records: Iterable,
    programme_start: date = PROGRAMME_START,
    tz: tzinfo | None = None,
) -> list[WeeklyMatchingSummary]:
    """
    Aggregate run records into one summary per programme week, oldest first.

    Aware timestamps are converted to `tz` before the date is taken, so a run just
    after local midnight on a Monday falls in the new week (ISSUES.md ISSUE-035).
    `tz` defaults to Django's configured TIME_ZONE; pass the programme's timezone
    explicitly when it differs from the server setting.
    """
    weeks: dict[int, WeeklyMatchingSummary] = {}
    for record in records:
        week = programme_week(_local_date(record.started_at, tz), programme_start)
        start = programme_start + timedelta(weeks=week - 1)
        summary = weeks.setdefault(week, WeeklyMatchingSummary(week, start, start + timedelta(days=6)))
        summary.runs_total += 1
        summary.requirements.add(record.requirement_id)
        summary.candidates_submitted += record.candidates_submitted
        if record.status == "completed":
            summary.runs_completed += 1
            summary.candidates_ranked += record.candidates_ranked
            summary.candidates_excluded += record.candidates_excluded
            summary.candidates_insufficient_data += record.candidates_insufficient_data
            if record.configuration_status == "unapproved":
                summary.runs_with_unapproved_config += 1
        else:
            summary.runs_failed += 1
            summary.failure_codes[record.error_code or "unknown"] += 1
    return [weeks[w] for w in sorted(weeks)]
