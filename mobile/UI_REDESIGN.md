# Staff app UI redesign

The first prototype used neutral Forui defaults, a stack of full-width buttons, repeated demo banners, and long pages for every task. It had no event-level navigation. Scanner scenarios crowded the admission flow, and primary actions scrolled out of view.

The redesign keeps Flutter, Forui, the backend-shaped mock transport, all three locales, and secure sessions. This is a native mobile app: Apple HIG and Material touch/navigation conventions take precedence over marketing-site styling.

## Structure

- Sign in: a focused form with inline validation, password visibility inside the field, a quiet reset link, and a compact language control.
- Assigned events: large readable heading, tappable event rows with date/venue hierarchy, pull to refresh, account access in the toolbar. No redundant Open buttons.
- Selected event: one workspace with Overview, Scan, and Guests bottom destinations. Event context stays visible. Back returns to event selection.
- Overview: one attendance summary, compact venue/date details, and one primary Scan action. Counts remain server-derived.
- Scan: framed camera stage, clear event context, a manual-entry sheet, and an isolated demo-code sheet. No wall of scenario buttons in the main screen.
- Result: explicit status and supporting icon, concise attendee details, fixed bottom admission/continue action. Reversal is secondary and requires confirmation.
- Guests: search as you type with debounce, compact tappable rows, readable status labels, pagination, and accessible empty/error feedback.
- Account: profile and language first; demo controls behind a separate screen; destructive logout action separated from preferences.

## Visual and interaction rules

Cool neutral surfaces with one restrained green accent, native system typography, 8-point spacing rhythm, 12–20 point radii, and 48-point minimum interactive targets. Functional status colors use both text and icons. Light/dark modes use semantic tokens. Motion is limited to native navigation and feedback, and respects reduced-motion settings.

Keep repeated controls near the bottom, preserve safe areas, scroll above keyboards, support large text and narrow screens, and label every icon action. No photos or decorative charts are needed for the operational flow. Loading/error states preserve task context. Never animate counters independently of a server response.

## Verify

Exercise sign-in, event selection, scan/admit, duplicate rejection, manual lookup, undo, language changes, offline errors, and logout. Check narrow widths, larger text, both color schemes, and simulator rendering. Physical camera behavior remains a separate device check.
