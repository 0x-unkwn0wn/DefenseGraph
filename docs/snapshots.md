# Snapshots

Snapshots provide lightweight historical comparison for the dashboard.

## Stored Data

Each `CoverageSnapshot` stores:

- name
- creation date
- optional metadata
- summary JSON

The MVP does not snapshot every technique row. It stores only aggregate values needed for trend comparison.

## Current Comparison

When at least one snapshot exists, DefenseGraph compares the live state against the latest snapshot and shows:

- real coverage delta
- tested coverage delta
- critical gap count delta

## Limitation

This is a summary-history feature, not a full time-series warehouse. It is intended for baseline comparisons and progress reviews.
