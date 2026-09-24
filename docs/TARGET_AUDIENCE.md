# TARGET_AUDIENCE_V3.md

## קהל יעד, פרסונות, אימוץ ומסחור — מערכת ארגונית לניהול מבדקים

**תאריך:** 19.09.2026  
**סטטוס:** גרסה מאוחדת להמשך אפיון MVP  
**בסיס:**  
- PRODUCT_ANALYSIS / PRODUCT_ANALYSIS_V4  
- TARGET_AUDIENCE.md  
- TARGET_AUDIENCE_CLAUDE.md  
- TARGET_AUDIENCE_GEMINI.md  

> עיקרון מנחה: המסמך מפריד בין שלושה צירים שונים:
>
> 1. **מי משתמש במערכת**
> 2. **מי מאפשר/מאשר את כניסתה לארגון**
> 3. **מי קונה או מתקצב אותה**
>
> בנוסף, כל הנחה שעדיין לא אומתה מסומנת במפורש כ-**[הנחה]** או **[החלטה פתוחה]**.

---

# 1. מטרת המסמך

מסמך זה נועד לתרגם את אפיון המוצר להחלטות פרקטיות לקראת MVP:

- למי בונים קודם
- אילו כאבים חייבים לפתור
- אילו טריגרים מפעילים שימוש
- אילו חסמים עלולים למנוע אימוץ או רכישה
- אילו בעלי עניין חייבים להיות מעורבים
- מה נדרש בפיילוט
- אילו רכיבים שייכים למוצר ואילו למסחור עתידי

---

# 2. Target Organization Profile

## 2.1 ארגון יעד ראשוני

המערכת מתאימה במיוחד לארגונים שבהם מבדקים הם תהליך ניהולי מחייב ולא פעילות אד-הוק.

מאפיינים אופייניים:

- ארגון בינוני או גדול
- מספר יחידות / אתרים / תהליכים / ספקים
- תוכנית מבדקים שנתית או רב-שנתית
- דרישות רגולטוריות / תקניות
- צורך במעקב פורמלי אחר Findings ו-Actions
- צורך ב-Traceability
- צורך בהרשאות ואבטחת מידע
- שימוש כיום במספר כלים במקביל

## 2.2 קהל יעד מקצועי

העדיפות הראשונית:

- תעופה
- ביטחון
- חלל
- תעשייה מפוקחת
- שרשראות אספקה המחויבות לדרישות איכות פורמליות

## 2.3 סוגי מבדקים רלוונטיים

- Internal Audits
- Supplier Audits
- Process Audits
- Product Audits
- Project Audits
- Special Process Audits
- Compliance Audits

לא נדרש לתמוך בכולם ב-MVP.

---

# 3. Stakeholder Map

יש להפריד בין ארבע קבוצות.

## 3.1 Core Users

משתמשים שעובדים במערכת באופן שוטף:

- Audit Programme Manager
- Lead Auditor
- Auditor
- Finding Owner
- Verifier / Closure Approver

## 3.2 Operational Secondary Users

משתמשים שנכנסים למערכת לצורך פעולה נקודתית:

- Auditee Representative
- Unit Manager
- Supplier Representative
- Viewer

## 3.3 Buying / Sponsorship Roles

- Champion
- Economic Buyer
- Executive Sponsor

## 3.4 Gatekeepers

- IT
- Information Security / Cyber
- Enterprise Architecture
- Procurement
- Legal / Compliance

---

# 4. Primary Product Personas — P0

ארבע הפרסונות הבאות הן ליבת ה-MVP.

## P0.1 Audit Programme Manager

### תפקיד
אחראי על תוכנית המבדקים, תעדוף, הקצאה, בקרה ומעקב.

### מטרות
- לדעת מה תוכנן, מה בוצע ומה באיחור
- לדעת אילו ממצאים דורשים התערבות
- לקבל מקור אמת אחד
- להציג תמונת מצב אמינה להנהלה
- למנוע מבדקים וממצאים "תקועים"

### Pain Points
- Excel שאינו משקף מצב אמת
- רדיפה ידנית אחרי מבקרים ובעלי ממצאים
- חוסר יכולת להבחין בין "בוצע" ל"נסגר"
- פיצול מידע בין Word, Outlook, SharePoint ומערכות נוספות
- קושי לזהות הישנות

### Usage Triggers
- בניית תוכנית שנתית
- פתיחת Audit
- הקצאת Lead Auditor
- חריגה מתאריך יעד
- ממצא משמעותי
- ממצא חוזר
- Management Review
- מבדק חיצוני מתקרב

### MVP Must-Have
- רשימת מבדקים
- סטטוס ברור
- בעלי תפקידים
- תאריכי יעד
- חריגות
- Dashboard בסיסי
- Drill-down
- Audit Trail

### Success Metric
המנהל יכול לענות תוך פחות מדקה:

> אילו מבדקים וממצאים דורשים טיפול עכשיו?

---

## P0.2 Lead Auditor

### תפקיד
מתכנן ומוביל את המבדק בפועל.

### מטרות
- להכין Audit במהירות
- לעבוד מול Checklist ו-Criteria
- לתעד Evidence
- לפתוח Findings
- לייצר Report ללא עבודה כפולה
- לעקוב עד Closure

### Pain Points
- העתקה חוזרת בין Word / Excel / Email
- קושי לקשר Requirement → Evidence → Finding
- שונות בין מבקרים
- Checklist לא מעודכן
- כתיבת Report מחדש

### Usage Triggers
- הקצאה למבדק
- תחילת הכנה
- התחלת Audit
- העלאת Evidence
- פתיחת Finding
- Completion
- Verification
- Closure Request

### MVP Must-Have
- Audit Workspace
- Scope
- Criteria
- Checklist
- Evidence
- Finding creation
- Report generation
- Status & history

### Success Metric
ניתן לבצע Audit מלא ללא צורך בקובץ Word/Excel נפרד.

---

## P0.3 Finding / Action Owner

### תפקיד
אחראי לבצע את הפעולות הנדרשות בעקבות ממצא.

### מטרות
- להבין מה נדרש
- לדעת Due Date
- להגיש Evidence
- למנוע הסלמה
- לדעת האם הטיפול התקבל

### Pain Points
- מיילים ללא הקשר
- דרישה לא ברורה
- תאריכי יעד לא עקביים
- שליחת Evidence מחדש
- חוסר ודאות לגבי Closure

### Usage Triggers
- Finding assigned
- Reminder
- Due Date approaching
- Overdue
- Evidence rejected
- Reopen
- Effectiveness Check required

### MVP Must-Have
- מסך פשוט
- Finding description
- Requirement
- Due Date
- Required Action
- Evidence upload
- Comments
- Status

### Success Metric
המשתמש לא צריך לשאול במייל:

> מה עוד חסר כדי לסגור?

---

## P0.4 Verifier / Closure Approver

### תפקיד
מאמת ביצוע, בודק אפקטיביות ומאשר Closure.

### מטרות
- להפריד בין ביצוע פעולה לבין אפקטיביות
- לשמור עצמאות בהחלטת הסגירה
- למנוע Closure מוקדם
- לתעד מי אישר ומה נבדק

### Pain Points
- Evidence מפוזר
- אין הפרדה בין Verification ל-Effectiveness
- אין תיעוד של Approval
- אין היסטוריית Reopen
- אין שקיפות על הארכות

### Usage Triggers
- Action completed
- Evidence submitted
- Effectiveness date reached
- Closure requested
- Reopen requested

### MVP Must-Have
- Evidence review
- Approve / Reject
- Verification result
- Effectiveness result
- Mandatory comment on rejection
- Audit Trail

### Success Metric
כל Closure ניתן להסבר ולשחזור בדיעבד.

---

# 5. Secondary Product Personas — P1/P2

## P1.1 Auditor / Audit Team Member

צריך:

- לראות רק את חלקו
- להזין Evidence
- להוסיף Observations / Findings
- לעבוד במקביל עם אחרים ללא דריסה

## P1.2 Auditee Representative

צריך:

- להבין מה נדרש
- להגיב
- לספק Evidence
- לעקוב אחרי Findings הקשורים אליו

UX צריך להיות פשוט משמעותית מזה של Lead Auditor.

## P1.3 Unit / Supplier / Project Manager

צריך:

- תמונת מצב בתחום אחריותו
- איחורים
- Findings משמעותיים
- Escalations

לרוב Viewer + Managerial Actions, לא Full Edit.

## P2.1 Executive Viewer

צריך:

- KPI
- חריגות
- ממצאים חוזרים
- Coverage
- מגמות

אינו צריך גישה תפעולית עמוקה.

---

# 6. Buying & Governance Personas

## B1 — Champion

### מי זה
לרוב:

- Quality Manager
- Audit Programme Manager
- Head of Quality

### תפקיד
- מזהה את הכאב
- מקדם את המוצר
- מגייס משתמשים לפיילוט
- מייצר Business Case

### מה חשוב לו
- שליטה
- שקיפות
- פחות עבודה ידנית
- Closed Loop
- Reporting

## B2 — Economic Buyer

### מי זה
עשוי להיות:

- VP Quality
- COO
- General Manager
- Business Unit Manager

### מה חשוב לו
- סיכון
- עלות
- ROI
- עמידה בדרישות
- הפחתת זמן אדמיניסטרטיבי
- יכולת ניהולית

### הוכחה נדרשת
- פיילוט
- KPI לפני/אחרי
- Case Study
- Reduction in overdue findings
- Reduction in reporting effort

## B3 — IT / InfoSec Gatekeeper

### מה חשוב לו
- Deployment
- SSO / MFA
- Access Control
- Encryption
- Logs
- Backup
- Data Classification
- Export Control
- API
- On-Prem / Private Cloud / Closed Network

### חסם
מערכת טובה פונקציונלית יכולה להיפסל לחלוטין אם אינה עומדת בדרישות אבטחת מידע.

## B4 — Procurement / Legal

### מה חשוב לו
- חוזה
- SLA
- זמינות תמיכה
- אחריות
- המשכיות
- הגנת מידע
- Exit / Data Export

### [הנחה]
אם המוצר יהפוך למסחרי, נדרש מסמך אבטחה, תנאי שירות ו-SLA.

---

# 7. Pain Points — ברמת המשתמש

## Pain 1 — אין Single Source of Truth

**בעיה:** המידע מפוזר.  
**MVP Response:** Audit Record אחד.

## Pain 2 — מעקב ידני אחרי Findings

**בעיה:** Owner, Due Date ו-Evidence מנוהלים ידנית.  
**MVP Response:** Finding Workflow + reminders + aging.

## Pain 3 — אין Closed Loop אמיתי

**בעיה:** Action מסומנת Completed בלי אימות אפקטיביות.  
**MVP Response:**

```text
Finding
→ Action
→ Evidence
→ Verification
→ Effectiveness
→ Closure
```

## Pain 4 — עבודה כפולה

**בעיה:** המידע נכתב שוב בדוח.  
**MVP Response:** Report נבנה מהמידע הקיים.

## Pain 5 — Traceability חלשה

**בעיה:** קשה לקשר דרישה ל-Evidence ול-Finding.  
**MVP Response:** Data Model עם Relationships מפורשים.

## Pain 6 — הרשאות לא מותאמות

**בעיה:** מידע רגיש נחשף רחב מדי.  
**MVP Response:** RBAC + Scope-based access + Security Classification בסיסי.

---

# 8. Pain Points — ברמת הארגון

- אין תמונת מצב ניהולית אמינה.
- קיים סיכון של Findings שנותרים פתוחים ללא בקרה.
- הוכחת Traceability דורשת עבודת הכנה ידנית.
- אין הבחנה ברורה בין Completed, Verified, Effective ו-Closed.
- המערכת הקיימת אינה בהכרח תומכת היטב בהרשאות / סיווג / Audit Trail.
- קיימת תלות באנשי מפתח ובקבצים.

---

# 9. Usage Triggers

אלו Events שמפעילים שימוש בפועל.

| Trigger | Persona | Action |
|---|---|---|
| Audit נוצר | Programme Manager | Assign / schedule |
| Audit הוקצה | Lead Auditor | Prepare |
| Audit מתחיל | Auditor | Execute |
| Gap זוהה | Auditor | Create Finding |
| Finding הוקצה | Owner | Plan Action |
| Due Date מתקרב | Owner | Update |
| Due Date עבר | Manager | Escalate |
| Action הושלמה | Verifier | Verify |
| Effectiveness date הגיע | Verifier | Check Effectiveness |
| כל Findings נסגרו | Approver | Close Audit |
| Management Review | Manager | Dashboard |

---

# 10. Purchase / Adoption Triggers

יש להפריד בין Use Trigger לבין סיבה שבגללה הארגון מחליט להכניס מערכת.

## Trigger 1 — מבדק חיצוני מתקרב
הארגון נדרש להוכיח Audit Programme, Findings, Actions, Closure ו-Evidence.

## Trigger 2 — ממצא שנשכח / הסלמה
אירוע שבו התברר שממצא ישן לא טופל.

## Trigger 3 — גידול בכמות המבדקים / ספקים
Excel כבר אינו מספיק.

## Trigger 4 — Management Pressure
הנהלה דורשת Dashboard ו-KPI אמינים.

## Trigger 5 — החלפת מערכת
הזדמנות בעת QMS replacement, ERP upgrade או Digital Transformation.

## Trigger 6 — מנהל איכות חדש
**[הנחה לאימות]** מנהל חדש עשוי לחפש החלפה של תהליך ידני.

---

# 11. Adoption Barriers — משתמשים

## Barrier 1 — "Excel מספיק"
לא להתחרות ב-Excel על גמישות; להתחרות ב-Traceability, Closed Loop, Audit Trail, Permissions, Reminders ו-Status.

## Barrier 2 — המערכת מוסיפה עבודה
אם המשתמש צריך גם את המערכת וגם Word/Excel — ה-MVP נכשל.

## Barrier 3 — UX מורכב
נדרש Role-Based UX.

## Barrier 4 — התנגדות לתהליך חדש
המערכת צריכה ליישם את ה-Lifecycle הקיים, לא להמציא מתודולוגיה חדשה.

## Barrier 5 — חוסר אמון בנתונים
נדרש Audit Trail, Versioning, Status Rules ו-Ownership.

---

# 12. Purchase / Deployment Barriers

## Barrier 1 — Information Security
עלול להיות Blocker מוחלט.

נדרש:

- SSO
- MFA
- RBAC
- Logging
- Encryption
- Export controls
- Deployment model

## Barrier 2 — "יש לנו כבר מערכת"
המתחרה עשוי להיות ERP, QMS, SharePoint, Excel או פיתוח פנימי.

### מענה
לא למצב את המוצר כ-QMS מלא, אלא כ-Audit Management specialization.

## Barrier 3 — Integration Fear
הארגון חושש מעוד Data Island.

### מענה
- API-ready
- Integration Layer
- Import/Export
- Future SAP/PLM/HR connectors

## Barrier 4 — Migration
הלקוח לא רוצה להתחיל מאפס.

### MVP / Early Release
- Excel import
- Open Findings import
- Audit Plan import

## Barrier 5 — Deployment

**[החלטה פתוחה]**

נדרש להכריע:

- SaaS
- Private Cloud
- On-Prem
- Closed Network

---

# 13. MVP Persona Priorities

## P0 — חובה

1. Audit Programme Manager
2. Lead Auditor
3. Finding Owner
4. Verifier / Closure Approver

אם ארבעת התפקידים האלה לא יכולים לסיים תהליך מלא — ה-MVP אינו שלם.

## P1 — חשוב

5. Auditor
6. Auditee Representative
7. Unit / Supplier / Project Manager

## P2 — לאחר MVP

8. Executive Viewer
9. External Supplier User
10. Advanced System Admin
11. Risk Manager
12. Data Analyst

---

# 14. MVP User Journeys

## Journey 1 — Audit Creation & Execution

```text
Programme Manager
→ Create Audit
→ Assign Lead
→ Prepare
→ Execute
→ Complete
```

## Journey 2 — Finding Lifecycle

```text
Auditor
→ Create Finding
→ Assign Owner
→ Action
→ Evidence
→ Verification
→ Closure
```

## Journey 3 — Effectiveness

```text
Action Verified
→ Wait Period
→ Effectiveness Check
→ Effective / Reopen
```

## Journey 4 — Overdue

```text
Due Date
→ Reminder
→ Overdue
→ Escalation
→ Manager
```

## Journey 5 — Audit Closure

```text
Completed Audit
→ Check Findings
→ Check Actions
→ Check Verification
→ Check Effectiveness
→ Approve
→ Closed
```

---

# 15. MVP Acceptance Criteria — ברמת קהל היעד

ה-MVP ראוי לפיילוט רק אם:

- Programme Manager רואה מבדקים וחריגות במסך אחד.
- Lead Auditor מבצע Audit ללא קובץ מקביל הכרחי.
- Finding Owner רואה רק את הפעולות הרלוונטיות לו.
- Verifier יכול Approve / Reject Evidence.
- Effectiveness Check ניתן לתזמון.
- המערכת לא מאפשרת לסגור Audit עם Finding פתוח.
- כל שינוי מהותי מתועד.
- הרשאות מונעות גישה לא מורשית.
- Report נבנה מהמידע הקיים.

---

# 16. Early Adopters / Pilot Structure

## קבוצת פיילוט מומלצת

- 1 Audit Programme Manager
- 2–4 Lead Auditors
- 5–10 Finding Owners
- 1–2 Verifiers
- 1 Quality Manager
- IT / InfoSec Reviewer

## סוג Audit מומלץ לפיילוט

לבחור אחד בלבד:

- Internal Audit
או
- Supplier Audit

### קריטריונים לבחירה
- תהליך חוזר
- יש Findings
- יש Follow-up
- היקף נשלט
- קיימת היסטוריה להשוואה

---

# 17. Adoption Flow

## Product Flow

```text
Audit Manager
→ Lead Auditor
→ Finding Owner
→ Verifier
```

## Adoption Flow

```text
Champion
→ Economic Buyer
→ IT / InfoSec
→ Deployment
```

שני המסלולים חייבים לעבוד במקביל.

---

# 18. Assumptions & Open Decisions

## [החלטה פתוחה]

- מי בפועל הוא Economic Buyer
- Cloud / On-Prem / Closed Network
- האם Supplier Users ייכנסו ישירות
- האם יש צורך ב-Multi-Tenancy
- האם SSO/MFA חובה ב-MVP
- האם Root Cause נדרש לכל Finding
- אילו Findings דורשים Effectiveness Check
- האם עברית + אנגלית נדרשות מהיום הראשון

## [הנחה לאימות]

- Excel הוא המתחרה המרכזי בפלח הראשוני
- מנהל איכות הוא ה-Champion הטבעי
- Security Review הוא Gate מוקדם
- Import from Excel יפחית חסם אימוץ
- Internal/Supplier Audit הם סוגי הפיילוט הטובים ביותר

---

# 19. Commercial GTM Appendix — אופציונלי

> סעיף זה רלוונטי רק אם המערכת מוגדרת כמוצר מסחרי B2B.  
> אם מדובר במערכת פנים-ארגונית, אין להשתמש בו כהחלטת מוצר.

## 19.1 Beachhead Candidate

**[הנחה לאימות]**

יצואנים וספקי משנה בתחום ביטחון / תעופה בישראל, בגודל בינוני.

### למה ייתכן שזה פלח פתיחה טוב
- תהליכי איכות פורמליים
- צורך ב-Traceability
- נגישות יחסית
- פחות Integration complexity מארגון Tier-1 גדול

### Kill Criteria
ההנחה תידחה אם:

- אין תקציב ייעודי
- רוב הארגונים עובדים היטב עם ERP/QMS קיים
- דרישות אבטחה חוסמות MVP
- Pain אינו מספיק חזק

## 19.2 Design Partners

המלצה:

- 2–3 ארגונים
- Pilot של 60–90 יום
- Use Case אחד
- Feedback structured
- Case Study

## 19.3 Buying Committee

- Champion
- Economic Buyer
- IT / InfoSec
- Procurement / Legal
- Users

## 19.4 GTM Channels

- Direct B2B
- Design Partners
- Professional Network
- Consultants
- Conferences
- Professional Content

## 19.5 Commercial Message

### Economic Buyer
> Reduce audit risk, overdue findings and manual reporting effort.

### Champion
> Stop building audit status manually.

### Finding Owner
> See exactly what is required and close it in one place.

### InfoSec
> Controlled deployment, permissions, logging and traceability.

---

# 20. מה לא להכניס למסמך הליבה כרגע

כדי למנוע ערבוב בין Product Definition למסחור, אין לקבע עדיין:

- TAM
- מחיר
- Packaging
- SaaS tiers
- Reseller Model
- Marketplace Strategy
- Global Expansion
- Certification Body Partnerships

אלו שייכים למסמך GTM / BUSINESS_MODEL נפרד לאחר אימות שוק.

---

# 21. מסקנה אופרטיבית

## לפיתוח

יש לבנות קודם עבור:

```text
Audit Programme Manager
→ Lead Auditor
→ Finding Owner
→ Verifier
```

## לאימוץ

יש לתת מענה ל:

```text
Champion
→ Economic Buyer
→ IT / InfoSec
```

## ה-MVP צריך להוכיח

```text
Audit Planned
→ Audit Executed
→ Finding Created
→ Action Completed
→ Verified
→ Effectiveness Checked
→ Finding Closed
→ Audit Closed
```

כל פיצ'ר שאינו תומך ישירות באחד מהמסלולים הללו צריך לקבל עדיפות נמוכה יותר ב-MVP.

---

# 22. הצעד הבא

המסמך הבא צריך להיות:

**MVP_USER_STORIES.md**

הוא צריך לתרגם את ארבע פרסונות P0 ואת חמשת ה-User Journeys ל-Backlog מפורט:

```text
As a [persona]
I want to [action]
So that [business value]

Acceptance Criteria:
- ...
- ...
```

זה יהיה החיבור הישיר בין הגדרת קהל היעד לבין תכנון הפיתוח.
