# DESIGN_SYSTEM_V2.md

## Clear Trust — מערכת שפה ויזואלית למערכת ניהול מבדקים ארגונית

**תאריך:** 19.09.2026  
**סטטוס:** גרסה מאוחדת ומומלצת ל-MVP  
**בסיס:**  
- `PRODUCT_ANALYSIS.md`
- `TARGET_AUDIENCE.md`
- `DESIGN_SYSTEM.md`
- `DESIGN_SYSTEM_CLAUDE.md`
- `DESIGN_SYSTEM_GEMINI.md`

> מטרת המסמך: להגדיר מערכת עיצוב ישימה ל-Figma ול-Frontend, עם הפרדה ברורה בין Foundations, Semantic Language, Components, Accessibility, Output Channels ו-Design Tokens.

---

# PART A — FOUNDATIONS

# 1. Design Concept

## Clear Trust — אמינות שקופה

המערכת מיועדת לסביבה מקצועית ומבוקרת שבה משתמשים צריכים להבין במהירות:

- מה הסטטוס
- מה דורש פעולה
- מי אחראי
- מה הראיות
- מה השתנה
- מי אישר
- האם טיפול אכן אומת ונמצא אפקטיבי

השפה הוויזואלית צריכה לשדר:

- אמינות
- שליטה
- דיוק
- שקט ויזואלי
- מקצועיות
- אבטחת מידע
- עקיבות

---

# 2. Design Principles

1. **Clarity over decoration** — בהירות לפני קישוט.
2. **Control over animation** — תנועה פונקציונלית בלבד.
3. **Traceability over visual novelty** — עקיבות חשובה יותר מ"חידוש".
4. **Role-first UX** — צפיפות ומבנה משתנים לפי תפקיד.
5. **Green is earned** — ירוק מופיע רק לאחר אימות/סגירה אמיתית.
6. **Status is not severity** — סטטוס, חומרה ואיחור הם שלוש שכבות נפרדות.
7. **Quiet urgency** — אדום שמור לסיכון אמיתי.
8. **Trust must be visible** — מי, מתי ולמה צריכים להיות גלויים.
9. **Never color-only** — משמעות תמיד כוללת טקסט, אייקון או שניהם.
10. **RTL-first** — עברית היא ברירת תכנון, לא התאמה מאוחרת.

---

# 3. Brand Personality

## רצוי

- מקצועי
- מדויק
- אמין
- מודרני
- מאופק
- טכנולוגי
- לא מאיים
- תכליתי

## להימנע

- מראה "צעצועי"
- צבעוניות יתר
- גרדיאנטים דקורטיביים
- צללים כבדים
- כרטיסיות שיווקיות
- אנימציות קישוטיות
- שימוש יתר באדום
- שימוש בירוק ל-"In Progress"

---

# 4. Core Color Palette

## 4.1 Primary — Aero Blue

| Token | HEX | שימוש |
|---|---|---|
| `blue-50` | `#EFF4FF` | רקע פעולה/סטטוס עדין |
| `blue-100` | `#DCE6FF` | selected / issued |
| `blue-200` | `#BFD0FF` | גבולות |
| `blue-300` | `#93AEFF` | accents |
| `blue-400` | `#6386FA` | dark mode links |
| `blue-500` | `#3F63EE` | action in dark |
| `blue-600` | `#2C4BD1` | Primary CTA / links / focus |
| `blue-700` | `#253DAA` | Hover |
| `blue-800` | `#22357F` | Pressed |
| `blue-900` | `#1D2C5E` | headers |
| `blue-950` | `#121B3C` | dark hero |

### פסיכולוגיה
אמון, סמכות, יציבות, דיוק ושליטה.

---

## 4.2 Neutral — Slate Ink

| Token | HEX | שימוש |
|---|---|---|
| `slate-0` | `#FFFFFF` | Surface |
| `slate-25` | `#F9FAFC` | Subtle background |
| `slate-50` | `#F3F5F9` | Page background |
| `slate-100` | `#E8ECF2` | Disabled/subtle |
| `slate-200` | `#D5DBE5` | Borders |
| `slate-300` | `#B4BDCB` | Secondary border |
| `slate-400` | `#8592A6` | Input border |
| `slate-500` | `#5F6C80` | Tertiary text |
| `slate-600` | `#465165` | Secondary text |
| `slate-700` | `#343E51` | Strong secondary |
| `slate-800` | `#232C3C` | Tooltip / dark surface |
| `slate-900` | `#161D2B` | Primary text / Sidebar |
| `slate-950` | `#0D131E` | Dark background |

---

## 4.3 Active Process — Signal Teal

| Token | HEX | שימוש |
|---|---|---|
| `teal-50` | `#E6F8F7` | Active background |
| `teal-100` | `#C2EEEC` | progress |
| `teal-300` | `#5FD3CE` | dark accents |
| `teal-500` | `#12A9A3` | charts |
| `teal-600` | `#087F7B` | active action |
| `teal-700` | `#0A6E6C` | active text |

### פסיכולוגיה
תהליך פעיל, התקדמות, שקט תפעולי.

---

# 5. Semantic Colors

## Success

| Token | HEX |
|---|---|
| `green-50` | `#E8F6EE` |
| `green-100` | `#C9EBD8` |
| `green-500` | `#23A15C` |
| `green-600` | `#1B8449` |
| `green-700` | `#17683B` |
| `green-800` | `#135332` |

**שימוש:** Closed, Verified, Effective.

---

## Warning

| Token | HEX |
|---|---|
| `amber-50` | `#FFF6E0` |
| `amber-100` | `#FFE8B0` |
| `amber-500` | `#F5A30A` |
| `amber-600` | `#D98A00` |
| `amber-700` | `#A86500` |
| `amber-800` | `#7A4A00` |

**שימוש:** Pending, Due Soon, waiting.

---

## Danger

| Token | HEX |
|---|---|
| `red-50` | `#FDECEC` |
| `red-100` | `#FAD0D0` |
| `red-500` | `#E5484D` |
| `red-600` | `#C93036` |
| `red-700` | `#A4242A` |
| `red-800` | `#7F1D22` |

**שימוש:** Overdue, Major risk, failed verification, destructive actions.

---

## Exception / Reopened

| Token | HEX |
|---|---|
| `violet-50` | `#F3EEFF` |
| `violet-100` | `#E3D8FF` |
| `violet-500` | `#7C5CE0` |
| `violet-600` | `#6844CC` |
| `violet-700` | `#5334A3` |

**שימוש:** Reopened / exceptional workflow.

---

# 6. Typography

## 6.1 Main Font

### מומלץ: Heebo

```css
font-family: "Heebo", system-ui, "Segoe UI", Arial, sans-serif;
```

### נימוק
- עברית + לטינית באותה משפחה
- מתאים לממשק צפוף
- קריא בטפסים וטבלאות
- מתאים לפריסה מקומית ב-On-Prem / Closed Network
- לא דורש תלות ב-CDN

## 6.2 Technical IDs

```css
font-family: ui-monospace, "IBM Plex Mono", "Roboto Mono", Consolas, monospace;
```

שימוש:
- Audit ID
- Finding ID
- סעיפי תקן
- Revision
- System IDs

---

# 7. Typography Scale

| Token | Size / Line Height | Weight | שימוש |
|---|---|---|---|
| `display` | 36 / 44 | 700 | שיווק / login |
| `h1` | 28 / 36 | 700 | Page title |
| `h2` | 22 / 30 | 600 | Section |
| `h3` | 18 / 26 | 600 | Card title |
| `h4` | 16 / 24 | 600 | Sub-section |
| `body-l` | 16 / 26 | 400 | Comfortable |
| `body-m` | 14 / 22 | 400 | Compact |
| `label` | 14 / 20 | 500 | Labels |
| `caption` | 12 / 18 | 500 | Meta |
| `kpi` | 32 / 40 | 700 | KPI |
| `mono` | 13 / 20 | 500 | IDs |

### כללים לעברית
- ללא Italic
- ללא Uppercase
- ללא letter-spacing משמעותי
- line-height נדיב
- ניסוח כפתורים בציווי ברור

---

# 8. Spacing, Radius, Shadow

## Base Unit
`4px`

## Spacing
`4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64`

## Radius

| Token | Value |
|---|---:|
| `sm` | 4px |
| `md` | 8px |
| `lg` | 12px |
| `full` | 999px |

## Shadows

```css
--shadow-1: 0 1px 2px rgba(13,19,30,.06), 0 1px 3px rgba(13,19,30,.08);
--shadow-2: 0 4px 12px rgba(13,19,30,.10);
--shadow-3: 0 12px 32px rgba(13,19,30,.16);
```

---

# 9. Grid & Density

## Layout

- 12-column grid
- Max content width: `1440px`
- Desktop padding: `32px`
- Tablet padding: `24px`
- Mobile padding: `16px`

## Form width

- Narrative forms: `720–960px`
- Dashboard / Tables: full available width

## Density Modes

### Compact
ל:
- Audit Programme Manager
- Lead Auditor

Values:
- Controls: `32–36px`
- Table rows: `40px`
- Text: `14px`

### Comfortable
ל:
- Finding Owner
- Auditee
- Verifier

Values:
- Controls: `44–48px`
- Table rows: `56px`
- Text: `16px`

---

# PART B — SEMANTIC LANGUAGE

# 10. Audit Lifecycle Colors

| Status | Background | Text | Semantic |
|---|---|---|---|
| Draft | `#E8ECF2` | `#343E51` | neutral |
| Planned | `#EFF4FF` | `#253DAA` | formal |
| Issued | `#DCE6FF` | `#22357F` | formal |
| In Progress | `#E6F8F7` | `#0A6E6C` | active |
| Completed | `#FFF6E0` | `#7A4A00` | waiting for closure |
| Closed | `#E8F6EE` | `#17683B` | final verified |
| Postponed | `#E8ECF2` | `#465165` | inactive |
| Cancelled | `#E8ECF2` | `#465165` | inactive |
| Reopened | `#F3EEFF` | `#5334A3` | exception |

### כלל
`Completed` אינו ירוק.  
רק `Closed` מקבל ירוק.

---

# 11. Finding Lifecycle

## משפחות צבע

| Family | Stages | Color |
|---|---|---|
| Open | Open | Amber |
| In Treatment | Containment / RCA / Action / Implementation | Teal |
| Verification | Pending Verification / Pending Effectiveness | Blue |
| Closed | Closed | Green |
| Exception | Reopened | Violet |
| Inactive | Cancelled / Waived | Gray |

---

# 12. Status ≠ Severity ≠ Time

## Workflow Status
איפה הפריט נמצא בתהליך.

## Severity
כמה משמעותי הממצא.

## Temporal Condition
האם הוא בזמן, מתקרב ליעד או באיחור.

### דוגמה

```text
Major | In Treatment | Overdue 12 days
```

שלושת הממדים חייבים להיות מוצגים בנפרד.

---

# 13. Severity

> שמות הסיווגים הסופיים עדיין תלויים בהגדרת הארגון.

| Severity | Style |
|---|---|
| Major | `#C93036` + white |
| Minor | `#FFF6E0` / `#7A4A00` |
| Observation | `#EFF4FF` / `#253DAA` |

---

# 14. Due / Overdue

| Condition | Style |
|---|---|
| On time | neutral |
| Due soon | Amber + clock |
| Overdue | Red + alarm icon + number of days |
| Extension approved | Clock-plus |

### כלל
Overdue הוא overlay על הסטטוס, לא סטטוס נפרד.

---

# 15. Security Classification

לכל אובייקט רלוונטי ניתן להציג:

- classification label
- lock icon
- export restriction
- audience restriction

### כלל
הייצוג צריך להיות configurable לפי מדיניות הלקוח.

---

# PART C — COMPONENTS

# 16. Buttons

## Primary

- Background: `#2C4BD1`
- Text: `#FFFFFF`
- Height: `40px`
- Radius: `8px`
- Hover: `#253DAA`
- Pressed: `#22357F`

שימוש:
- Save
- Submit
- Send for verification
- Approve closure

### כלל
"אשר סגירה" הוא Primary כחול, לא ירוק.

---

## Secondary

- Background: `#FFFFFF`
- Border: `#B4BDCB`
- Text: `#232C3C`

---

## Ghost

- Background: transparent
- Text: `#253DAA`

---

## Danger

- Background: `#C93036`
- Text: white

שימוש:
- Delete
- Cancel Audit
- Revoke Access

---

## Danger Outline

לפעולות כמו:
- Reject Evidence

דורש נימוק.

---

# 17. Cards

## Standard

- Background: `#FFFFFF`
- Border: `1px solid #D5DBE5`
- Radius: `8px`
- Padding: `16px` Compact / `24px` Comfortable
- Shadow: `shadow-1`

## Status Card

`border-inline-start: 4px solid var(--status-color)`

## KPI Card

- value
- label
- optional trend
- clickable drill-down

### כלל
אין Card בתוך Card.

---

# 18. Inputs

## Default

- Height: `40px` Compact / `48px` Comfortable
- Border: `#8592A6`
- Background: white
- Radius: `8px`
- Text: `#161D2B`
- Font size: `16px`

## Focus

- Border: `#2C4BD1`
- Focus ring גלוי

## Error

- Border: `#C93036`
- Error text: `#A4242A`
- icon + text

## Disabled

- Background: `#F3F5F9`
- Text: `#5F6C80`

## Read-only

- Background: `#F3F5F9`
- Dashed border

---

# 19. Textarea

שימוש:
- Finding description
- Root cause
- Corrective action
- Verification notes

Minimum:
- `96px`

Narrative:
- `160px`

---

# 20. Select / Combobox

- searchable מעל ~8 אפשרויות
- keyboard accessible
- labels קבועים
- multi-select עם chips

---

# 21. Status Badges

- Pill
- Height: 24 / 28px
- Padding: `4px 8px`
- Font: `12px / 600`
- icon + text
- background light / foreground dark

---

# 22. Tables

## חובה
- Sort
- Filter
- Search
- Sticky header
- Pagination
- Column customization
- Export לפי הרשאה

## Style
- Header: `#F3F5F9`
- Row border: `#D5DBE5`
- Hover: `#F9FAFC`
- Selected: `#EFF4FF`

### כלל
לא לצבוע שורה שלמה באדום בגלל Overdue.

---

# 23. Tabs

- Active underline: `2px #2C4BD1`
- Minimum height Comfortable: `44px`

---

# 24. Alerts / Banners

| Type | Background | Text |
|---|---|---|
| Info | `#EFF4FF` | `#22357F` |
| Success | `#E8F6EE` | `#135332` |
| Warning | `#FFF6E0` | `#7A4A00` |
| Error | `#FDECEC` | `#7F1D22` |

---

# 25. Modals

שימוש:
- confirmation
- critical approval
- quick edit

לא לתהליך ארוך.

Destructive / Reopen:
- impact summary
- reason field לפי צורך
- explicit CTA

---

# 26. File Upload / Evidence

- dashed border
- drag & drop
- file list
- size
- classification
- remove action
- scan/validation state אם קיים

---

# 27. Progress / Stepper

- Track: `#E8ECF2`
- Active: Teal
- Verified complete: Green
- Completed-but-not-closed: not green

---

# 28. Timeline / Audit Trail

היסטוריה צריכה להיות Human-readable.

### לא
```text
status: 3 → 4
```

### כן
```text
19.09.2026 14:32
יוסי כהן
שינה סטטוס מ-"ממתין לאימות"
ל-"ממתין לבדיקת אפקטיביות"
```

---

# 29. Notifications

## Toast
לפעולה רגעית.

## Banner
לבעיה הדורשת פעולה.

## Email
ל-triggers תפעוליים.

---

# PART D — ACCESSIBILITY

# 30. Accessibility Target

**WCAG 2.2 AA**

חובה:

- Contrast ≥ 4.5:1 לטקסט רגיל
- Contrast ≥ 3:1 לרכיבי UI
- Keyboard navigation
- Visible focus
- Labels לכל input
- Error text
- No color-only semantics
- `prefers-reduced-motion`
- Logical tab order
- 44px touch targets במסכי Comfortable

---

# 31. Focus

```css
box-shadow:
  0 0 0 2px #fff,
  0 0 0 4px #2C4BD1;
```

---

# 32. RTL / LTR

## Root

```html
<html lang="he" dir="rtl">
```

## CSS

להשתמש ב:
- `margin-inline-start`
- `padding-inline`
- `border-inline-start`
- `text-align: start`

לא ב:
- left/right hardcoded

## Mixed Content

IDs, emails, URLs, clauses:

```html
<bdi>AUD-2026-0042</bdi>
```

או:

```css
unicode-bidi: isolate;
direction: ltr;
```

## User-generated text
`dir="auto"`

---

# PART E — OUTPUT CHANNELS

# 33. Email

- Width: `600px`
- `dir="rtl"`
- short title
- status
- required action
- due date
- one primary CTA
- direct deep link

### כלל
Email הוא חלק מה-UX, במיוחד עבור Finding Owner.

---

# 34. PDF / Print

- A4
- embedded local font
- classification
- page numbers
- export timestamp
- readable in grayscale
- status includes text/icon, not color only
- optional watermark

---

# 35. Export

בהתאם להרשאה:

- PDF
- Word
- CSV/Excel
- Attachment download

### UX
אם פעולה אסורה, עדיף להציג סיבה ולא רק להעלים אפשרות.

---

# PART F — DESIGN TOKENS

# 36. Core CSS Tokens

```css
:root {
  --blue-50:#EFF4FF;
  --blue-100:#DCE6FF;
  --blue-200:#BFD0FF;
  --blue-300:#93AEFF;
  --blue-400:#6386FA;
  --blue-500:#3F63EE;
  --blue-600:#2C4BD1;
  --blue-700:#253DAA;
  --blue-800:#22357F;
  --blue-900:#1D2C5E;
  --blue-950:#121B3C;

  --slate-0:#FFFFFF;
  --slate-25:#F9FAFC;
  --slate-50:#F3F5F9;
  --slate-100:#E8ECF2;
  --slate-200:#D5DBE5;
  --slate-300:#B4BDCB;
  --slate-400:#8592A6;
  --slate-500:#5F6C80;
  --slate-600:#465165;
  --slate-700:#343E51;
  --slate-800:#232C3C;
  --slate-900:#161D2B;
  --slate-950:#0D131E;

  --teal-50:#E6F8F7;
  --teal-100:#C2EEEC;
  --teal-300:#5FD3CE;
  --teal-500:#12A9A3;
  --teal-600:#087F7B;
  --teal-700:#0A6E6C;

  --green-50:#E8F6EE;
  --green-100:#C9EBD8;
  --green-500:#23A15C;
  --green-600:#1B8449;
  --green-700:#17683B;
  --green-800:#135332;

  --amber-50:#FFF6E0;
  --amber-100:#FFE8B0;
  --amber-500:#F5A30A;
  --amber-600:#D98A00;
  --amber-700:#A86500;
  --amber-800:#7A4A00;

  --red-50:#FDECEC;
  --red-100:#FAD0D0;
  --red-500:#E5484D;
  --red-600:#C93036;
  --red-700:#A4242A;
  --red-800:#7F1D22;

  --violet-50:#F3EEFF;
  --violet-100:#E3D8FF;
  --violet-500:#7C5CE0;
  --violet-600:#6844CC;
  --violet-700:#5334A3;

  --bg-page:var(--slate-50);
  --bg-surface:var(--slate-0);
  --text-primary:var(--slate-900);
  --text-secondary:var(--slate-600);
  --border-subtle:var(--slate-200);
  --border-input:var(--slate-400);

  --action-bg:var(--blue-600);
  --action-bg-hover:var(--blue-700);
  --action-bg-active:var(--blue-800);

  --font-sans:"Heebo",system-ui,"Segoe UI",Arial,sans-serif;
  --font-mono:ui-monospace,"IBM Plex Mono","Roboto Mono",Consolas,monospace;

  --space-1:4px;
  --space-2:8px;
  --space-3:12px;
  --space-4:16px;
  --space-5:20px;
  --space-6:24px;
  --space-8:32px;
  --space-10:40px;
  --space-12:48px;
  --space-16:64px;

  --radius-sm:4px;
  --radius-md:8px;
  --radius-lg:12px;
  --radius-full:999px;

  --shadow-1:0 1px 2px rgba(13,19,30,.06),0 1px 3px rgba(13,19,30,.08);
  --shadow-2:0 4px 12px rgba(13,19,30,.10);
  --shadow-3:0 12px 32px rgba(13,19,30,.16);
}
```

---

# 37. Status Tokens

```css
--st-draft-bg:var(--slate-100);
--st-draft-fg:var(--slate-700);

--st-planned-bg:var(--blue-50);
--st-planned-fg:var(--blue-700);

--st-issued-bg:var(--blue-100);
--st-issued-fg:var(--blue-800);

--st-progress-bg:var(--teal-50);
--st-progress-fg:var(--teal-700);

--st-waiting-bg:var(--amber-50);
--st-waiting-fg:var(--amber-800);

--st-closed-bg:var(--green-50);
--st-closed-fg:var(--green-700);

--st-reopened-bg:var(--violet-50);
--st-reopened-fg:var(--violet-700);

--flag-overdue-fg:var(--red-700);
```

---

# APPENDIX A — PERSONA DENSITY

# 38. Density by Persona

| Persona | Mode |
|---|---|
| Audit Programme Manager | Compact |
| Lead Auditor | Compact |
| Finding Owner | Comfortable |
| Auditee | Comfortable |
| Verifier | Comfortable |
| Executive Viewer | Comfortable |

---

# APPENDIX B — ANTI-PATTERNS

# 39. אסור

- ירוק ל-In Progress
- ירוק ל-Completed
- אדום לכל Finding
- צבע כמשמעות יחידה
- Placeholder במקום label
- Cards בתוך Cards
- כמה Primary Buttons באותו אזור
- italics בעברית
- hardcoded left/right
- CDN לגופנים/אייקונים בפריסה סגורה
- Modal לתהליך ארוך
- Dashboard עמוס צבע

---

# APPENDIX C — FUTURE THEMING

# 40. Dark Mode

לא ב-MVP.

יש להכין Tokens בלבד.

---

# 41. White Label

ניתן לשנות:
- Logo
- Primary brand blue
- Header branding

לא מומלץ לשנות:
- Success
- Warning
- Danger
- Exception

משום שהם חלק מהשפה הסמנטית.

---

# APPENDIX D — WHAT MOVES TO OTHER DOCUMENTS

הנושאים הבאים אינם חלק מליבת Design System:

## להעביר ל-`UI_INFORMATION_ARCHITECTURE.md`
- Audit Workspace
- Finding Workspace
- Navigation structure
- Tabs architecture
- Page hierarchy

## להעביר ל-`MVP_SCREEN_MAP.md`
- Persona home screens
- Screen list
- Screen-to-screen transitions

## להעביר ל-`MVP_USER_STORIES.md`
- User journeys
- Business rules
- Acceptance criteria

## להעביר ל-`COMPONENT_SPEC.md`
- states
- props
- behaviors
- validation
- interaction details

---

# 42. Design Freeze Checklist

לפני אישור מערכת העיצוב:

- [ ] עברית/אנגלית הוכרעו
- [ ] Heebo אושר
- [ ] Status colors אושרו
- [ ] Severity model אושר
- [ ] Security classification behavior אושר
- [ ] Compact/Comfortable נבדקו
- [ ] WCAG 2.2 AA נבדק
- [ ] RTL mixed content נבדק
- [ ] Email template נבדק
- [ ] PDF/Print נבדק
- [ ] 3 מסכי פיילוט נבדקו מול משתמשים

---

# 43. Recommended Next Step

לבנות שלושה prototypes בלבד לפני הרחבת UI:

1. **Audit Programme Board**
2. **Finding Owner — "מה נדרש ממני"**
3. **Verification Queue**

המטרה: לבדוק מול משתמשים אמיתיים את:

- צפיפות
- סטטוסים
- צבעים
- ניסוח
- סדר פעולות
- הבנת Closed Loop

ורק לאחר מכן להמשיך ליתר המסכים.
