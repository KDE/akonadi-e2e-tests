<!--
SPDX-FileCopyrightText: 2026 Dominique MICHEL <dominique.michel@enioka.com>

SPDX-License-Identifier: GPL-2.0-or-later
-->

# iTIP samples

We store iTIP samples from different providers here to make it easier to understand the differences in the generated
formats and behaviors.

[[_TOC_]]

## Content

We have exported the following samples:

1. invitation
1. invitation update
1. recurring invitation
1. recurring invitation update, single occurrence
1. recurring invitation update, all occurrences since the start
1. recurring invitation update, all occurrences since a specific occurrence

## Analysis

### Google

Single event:
- invitation [invitation](./google/invitation.ics)
- invitation update [update](./google/invitation-update.ics)

Recurring event:
- recurring invitation [invitation](google/rec-invitation.ics)
- recurring invitation update, single occurrence [update](google/rec-invitation-update-single.ics)
- recurring invitation update, all occurrences since the start [update](google/rec-invitation-update-all.ics) and [deletion](google/rec-invitation-update-all_delete-single.ics)
- recurring invitation update, all occurrences since a specific occurrence [update](google/rec-invitation-update-all-since_old.ics) and [new](google/rec-invitation-update-all-since_new.ics)

Notes:
- An update to an invitation sends the same iCalendar file with updated properties
- Sending a recurring (weekly) invitation uses the same format with an added `RRULE`
- An update to a specific occurrence of a recurring event is an iCalendar file without `RRULE`, and with an added
  `RECURRENCE-ID` for the date of that occurrence
- When updating all occurrences since the start, Google sends a new iCalendar file to delete any modified occurrences of
  that recurring event
- When updating all occurrences since a specific occurrence, the existing recurring event is given an end date, and a new
  recurring event is created
- Each new invitation update increments the `SEQUENCE` property of the event

### Microsoft

Single event:
- invitation [invitation](./microsoft/invitation.ics)
- invitation update [update](./microsoft/invitation-update.ics)

Recurring event:
- recurring invitation [invitation](microsoft/rec-invitation.ics)
- recurring invitation update, single occurrence [update](microsoft/rec-invitation-update-single.ics)
- recurring invitation update, all occurrences since the start [update](microsoft/rec-invitation-update-all.ics) and [deletion](microsoft/rec-invitation-update-all_delete-single.ics)
- recurring invitation update, all occurrences since a specific occurrence [update](microsoft/rec-invitation-update-all-since_old.ics) and [new](microsoft/rec-invitation-update-all-since_new.ics)

Notes:
- An update to an invitation sends the same iCalendar file with updated properties
- Sending a recurring (weekly) invitation uses the same format with an added `RRULE` and
  `X-MICROSOFT-CDO-INSTTYPE:1`
- An update to a specific occurrence of a recurring event is an iCalendar file without `RRULE`, and with an added
  `RECURRENCE-ID` for the date of that occurrence and `X-MICROSOFT-CDO-INSTTYPE:3`
- When updating all occurrences since the start, Microsoft sends a new iCalendar file to delete any modified occurrences
  of that recurring event
- When updating all occurrences since a specific occurrence, the existing recurring event is given an end date, and a new
  recurring event is created
- Each new invitation update increments the `SEQUENCE` and `X-MICROSOFT-CDO-APPT-SEQUENCE` properties of the event
- Microsoft seems to add many `MICROSOFT` properties, some of which appear to duplicate standard ones

### Akonadi

Single event:
- invitation [invitation](./akonadi/invitation.ics)
- invitation update [update](./akonadi/invitation-update.ics)

Recurring event:
- recurring invitation [invitation](akonadi/rec-invitation.ics)
- recurring invitation update, single occurrence [update](akonadi/rec-invitation-update-single.ics)
- recurring invitation update, all occurrences since the start [update](akonadi/rec-invitation-update-all.ics) and no deletion
- recurring invitation update, all occurrences since a specific occurrence: could not be tested because it crashes Kontact
  every time

Notes:
- An update to an invitation sends the same iCalendar file with updated properties
- Sending a recurring (weekly) invitation uses the same format with an added `RRULE` and a very verbose `VTIMEZONE`
- An update to a specific occurrence of a recurring event is an iCalendar file without `RRULE`, and with an added
  `RECURRENCE-ID` for the date of that occurrence
- When updating all occurrences since the start, it affects only non-modified occurrences
- Each new invitation update increments the `SEQUENCE` properties of the event


## Conclusion

Differences:

- When using Akonadi, editing a recurring event with a specific occurrence modified beforehand does not delete the
  modified occurrence, unlike Google and Microsoft.
