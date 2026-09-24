# PRODUCT_ANALYSIS_V3.md

## מערכת ארגונית לניהול מבדקים — גרסת אפיון מוצר מאוחדת

**תאריך:** 19.09.2026  
**סטטוס:** גרסת בסיס מאוחדת להמשך אפיון  
**בסיס:**  
- הסקיצות הידניות שצורפו בתחילת התהליך  
- PRODUCT_ANALYSIS.md  
- PRODUCT_ANALYSIS_CLADE_AND_GEMINI.md  
- מחקר השוואתי מול OASIS / IAQG, Intact, ActionBase, Intelex, ETQ ומסגרת ISO 19011

> עיקרון מנחה: מסמך זה מפריד בין **מה שאומת מתוך האפיון**, **מה שנדרש ארכיטקטונית כדי לאפשר צמיחה עתידית**, ו-**מה נדחה לשלב מאוחר יותר**.  
> פרטים שלא אומתו מתוך האפיון אינם מוצגים כאן כהחלטה סופית.

---

# 1. הגדרת המוצר

## 1.1 תמצית

המערכת היא פלטפורמה ארגונית לניהול מחזור החיים המלא של מבדקים:

**תכנון → הכנה → ביצוע → תיעוד ראיות → ממצאים → פעולות → אימות → סגירה → למידה ותכנון מחדש**

הגרסה הראשונה תתמקד בביצוע אמין, פשוט ומבוקר של מבדק מקצה לקצה.

הארכיטקטורה תיבנה כך שבעתיד המערכת תוכל להפוך ל:

> **Enterprise Audit Management & Intelligence Platform**

---

# 2. Value Proposition

## 2.1 הבעיה הארגונית

בארגונים גדולים, ובפרט בסביבות תעופה, ביטחון וחלל, תהליך המבדקים מפוצל לעיתים בין מספר כלים:

- Excel לתוכנית מבדקים
- Word / PDF לשאלונים ודוחות
- Outlook לזימונים והתראות
- SharePoint למסמכים
- מערכת נפרדת לממצאים / פעולות
- ERP / SAP לנתוני ספקים
- PLM למוצר / פרויקט
- מערכות HR להסמכות מבקרים
- מערכות חיצוניות כגון OASIS

התוצאה:

- אין מקור אמת יחיד
- קשה לדעת סטטוס אמיתי של מבדק
- קשה לעקוב אחר ממצאים והישנות
- קשה להבין האם תוכנית המבדקים מכסה סיכונים
- קיימת כפילות מידע
- תהליך תלוי באנשים ובקבצים
- קשה לשמור Traceability בין דרישה, ראיה, ממצא ופעולה

---

## 2.2 הצעת הערך לגרסת MVP

> **מערכת פשוטה ומבוקרת לניהול מלא של מחזור חיי מבדק — מתכנון, דרך ביצוע ואיסוף ראיות, ועד סגירת כל הממצאים.**

המערכת תאפשר:

- ישות מבדק אחת
- סטטוסים ברורים
- הקצאת גורמים אחראים
- שאלות / קריטריונים
- ראיות
- ממצאים
- פעולות
- דוח
- סגירה מותנית בכללי מערכת

---

## 2.3 חזון המוצר

> **מערכת הפעלה ארגונית למבדקים שמחברת בין Audit Universe, סיכונים, תוכנית מבדקים, מבקרים, דרישות, ראיות, ממצאים, פעולות מתקנות ו-Analytics — ומחזירה את תוצאות המבדקים לתכנון העתידי.**

---

# 3. עקרונות בידול

המערכת לא צריכה להיות:

- עוד כלי טפסים
- עוד מערכת משימות
- עוד מאגר דוחות
- עוד Action Tracker

היא צריכה להתבסס על ארבעה עקרונות:

## 3.1 Traceability מלאה

קשר ישיר בין:

**מבדק ↔ תהליך ↔ יחידה ↔ ספק ↔ מוצר ↔ פרויקט ↔ תקן ↔ סעיף ↔ שאלה ↔ ראיה ↔ ממצא ↔ פעולה ↔ אימות**

---

## 3.2 Lifecycle מנוהל

המבדק אינו מסמך.

הוא ישות בעלת מחזור חיים, כללי מעבר, אחריות, היסטוריה וסטטוס.

---

## 3.3 Closed Loop

ממצא לא מסתיים ברישום בדוח.

המערכת צריכה לוודא:

**ממצא → פעולה → ראיית ביצוע → אימות → סגירה**

---

## 3.4 Architecture Ready for Intelligence

גם אם AI ו-Risk Engine אינם חלק מה-MVP, מבנה הנתונים צריך לאפשר בעתיד:

- תכנון מבוסס סיכון
- זיהוי ממצאים חוזרים
- המלצה על היקף מבדק
- בניית שאלונים
- בחירת מבקרים
- ניתוח מגמות
- איתור אזורים שלא נבדקו

---

# 4. Audit Lifecycle — מכונת המצבים

המחזור שנראה באפיון הראשוני:

```text
בנייה
  ↓
תכנון
  ↓
יוצא
  ↓
בתהליך
  ↓
הסתיים
  ↓
סגור
```

יש להוסיף שלושה מצבים משלימים:

- נדחה
- בוטל
- נפתח מחדש

---

## 4.1 הגדרת הסטטוסים

### Draft / בנייה

מבדק נוצר אך עדיין אינו מחייב.

מאפיינים:

- ניתן לערוך Scope
- ניתן לערוך קריטריונים
- ניתן להחליף צוות
- ניתן למחוק לפי הרשאה

---

### Planned / תכנון

המבדק שויך לתוכנית מבדקים.

נדרשים לפחות:

- סוג מבדק
- יעד מבוקר
- Scope
- תאריך יעד
- Lead Auditor

---

### Issued / יוצא

המבדק מוכן לביצוע.

בשלב זה:

- הבסיס התכנוני ננעל
- שינוי מהותי דורש Version / Change Log
- ניתן לשלוח זימון / התראה

---

### In Progress / בתהליך

המבדק החל.

ניתן להזין:

- תשובות
- הערות
- ראיות
- Observations
- Findings

---

### Completed / הסתיים

הביצוע המקצועי הסתיים.

ייתכן שעדיין קיימים:

- ממצאים פתוחים
- פעולות פתוחות
- אימותים שטרם בוצעו

---

### Closed / סגור

המבדק נסגר פורמלית רק כאשר מתקיימים תנאי הסגירה.

מינימום:

- אין ממצאים פתוחים
- אין פעולות פתוחות
- הדוח אושר
- בוצע Closure על ידי גורם מורשה

---

### Reopened / נפתח מחדש

פתיחה מחדש תתאפשר רק:

- בהרשאה
- עם נימוק
- עם Audit Trail
- תוך שינוי סטטוס חזרה ל-Completed או In Progress לפי הצורך

---

# 5. Core Data Model

זהו השלב הקריטי ביותר לפני בניית UI.

## 5.1 ישויות ליבה

### Audit Programme

שדות עיקריים:

- מזהה תוכנית
- שנה / תקופה
- Owner
- סטטוס
- מטרות
- Scope ארגוני

---

### Audit

שדות עיקריים:

- Audit ID
- Audit Type
- Audit Programme
- Title
- Objective
- Scope
- Criteria
- Auditee / Audit Object
- Lead Auditor
- Team
- Planned Date
- Actual Date
- Status
- Report
- Closure Date

---

### Audit Type

דוגמאות עתידיות:

- Internal
- Supplier
- Process
- Product
- Project
- Special Process
- Compliance

המערכת לא חייבת ליישם את כולם ב-MVP, אך הישות צריכה להתקיים.

---

### Audit Object / Auditee

אובייקט המבקר.

יכול להיות:

- יחידה
- מחלקה
- תהליך
- ספק
- פרויקט
- מוצר
- אתר
- מערכת

---

### Standard

- Standard ID
- שם
- Revision
- Effective Date
- Status

---

### Clause / Requirement

- Standard
- Clause
- Requirement ID
- Title
- Active Version

---

### Audit Criterion

ישות שמייצגת את הקריטריון בפועל במבדק.

יכולה לקשר:

- תקן
- סעיף
- נוהל
- דרישת לקוח
- הוראה פנימית
- דרישה חוזית

---

### Checklist

- מזהה
- סוג
- Version
- Owner
- Status

---

### Checklist Question

- Question ID
- Criterion
- Text
- Guidance
- Required Evidence
- Order
- Status

---

### Evidence

Evidence חייב להיות ישות נפרדת.

שדות:

- Evidence ID
- Audit
- Question / Criterion
- מקור
- סוג
- תיאור
- Collector
- Date
- Attachment
- Sensitivity
- Linked Finding

---

### Finding

- Finding ID
- Audit
- Criterion
- Description
- Objective Evidence
- Classification
- Owner
- Due Date
- Status
- Closure Evidence

---

### Action

- Action ID
- Finding
- Owner
- Due Date
- Description
- Status
- Completion Evidence

---

### Auditor

המבקר אינו User בלבד.

שדות:

- Auditor ID
- User
- Organization
- Status

---

### Auditor Qualification

- Audit Type
- Standard
- Qualification
- Authorization
- Expiry Date
- Experience
- Status

---

### Audit Trail

כל שינוי מהותי:

- Object
- Field
- Previous Value
- New Value
- User
- Date/Time
- Reason

---

# 6. יחסים עיקריים

```text
Audit Programme
   1
   |
   |--- N Audit

Audit
   |--- N Criteria
   |--- N Questions
   |--- N Evidence
   |--- N Findings
   |--- N Auditors

Finding
   |--- N Actions

Standard
   |--- N Clauses

Criterion
   |--- 1..N Requirement Sources

Auditor
   |--- N Qualifications
```

נדרש לתכנן Many-to-Many במקומות הבאים:

- Audit ↔ Auditor
- Audit ↔ Standard
- Audit ↔ Process
- Audit ↔ Supplier
- Audit ↔ Project
- Question ↔ Requirement
- Finding ↔ Criterion

---

# 7. Finding Lifecycle

המלצה לגרסה הראשונה היא לנהל מחזור חיים מלא של ממצא, כולל שלב נפרד לבדיקת אפקטיביות.

```text
Open
  ↓
Containment / Immediate Correction
  ↓
Root Cause
  ↓
Corrective Action Planned
  ↓
Implementation
  ↓
Pending Verification
  ↓
Pending Effectiveness Check
  ↓
Closed
```

מצבים משלימים:

- Reopened
- Cancelled
- Accepted Risk / Waived — רק אם הארגון מאפשר זאת פורמלית ובאישור מתאים
- Extension Approved — מצב/דגל לניהול הארכת יעד מאושרת

---

## 7.1 מינימום שדות לממצא

- Finding ID
- Audit ID
- תיאור הממצא
- דרישה / קריטריון
- Objective Evidence
- Classification
- Owner
- Due Date
- Immediate Correction / Containment
- Root Cause
- Corrective Action
- Action Owner
- Action Due Date
- Implementation Evidence
- Verification Result
- Effectiveness Check Required
- Effectiveness Check Due Date
- Effectiveness Check Result
- Closure Evidence
- Closure Approver
- Closure Date
- Status
- Reopen Reason
- Extension History

---

## 7.2 הפרדה בין Verification לבין Effectiveness Check

### Verification
עונה על השאלה:

> האם הפעולה שהוגדרה אכן בוצעה כפי שתוכנן?

דוגמאות:
- נוהל עודכן
- הדרכה בוצעה
- שינוי תהליך יושם
- מסמך תוקן
- פעולה טכנית הושלמה

### Effectiveness Check
עונה על השאלה:

> האם הפעולה שבוצעה אכן פתרה את הבעיה ומנעה הישנות?

בדיקת האפקטיביות יכולה לכלול:

- בדיקה חוזרת
- דגימה
- מבדק מעקב
- סקירת KPI
- בדיקת הישנות ממצא
- בחינת נתוני NCR / תלונות / חריגות
- ראיות תפעוליות נוספות

יש להגדיר מראש עבור כל ממצא האם נדרשת בדיקת אפקטיביות ומהו מועד הבדיקה.

---

## 7.3 כלל סגירה

מבדק לא יכול לעבור ל-Closed אם מתקיים אחד מהבאים:

- קיים Finding שאינו Closed
- קיימת Action פתוחה
- Verification נדרש וטרם בוצע
- Effectiveness Check נדרש וטרם הושלם
- קיימת חריגה מתאריך יעד שלא טופלה
- הדוח טרם אושר על ידי הגורם המוסמך

---

## 7.4 Finding Follow-up & Control

המערכת תכלול שכבת מעקב ובקרה ייעודית לממצאים:

- Aging לפי גיל ממצא
- Overdue Indicator
- תזכורות לפני Due Date
- התראות חריגה
- Escalation למנהל
- בקשת הארכת יעד
- אישור/דחיית הארכה
- ניהול סיבות לעיכוב
- Reopen עם נימוק
- היסטוריית סטטוסים
- Dashboard לפי:
  - מבדק
  - יחידה
  - ספק
  - Owner
  - חומרה
  - גיל
  - סטטוס
  - ממצאים חוזרים

---


# 8. Roles & Permissions

אין לקבע כרגע את המודל של:

- Admin
- Editor
- Auditee

כמודל סופי.

במקום זאת יש להגדיר Role Model גמיש, המבוסס על RBAC ובמידת הצורך גם על ABAC.

## 8.1 תפקידים מומלצים להגדרה

- System Admin
- Audit Programme Manager
- Lead Auditor
- Auditor
- Auditee Representative
- Finding Owner
- Approver
- Viewer

---

## 8.2 הרשאות

נדרשת הפרדה בין:

- Read
- Create
- Edit
- Approve
- Close
- Reopen
- Assign
- Export

---

## 8.3 רמות הגבלת מידע

ייתכן צורך ב:

- Organizational Unit
- Project
- Supplier
- Audit
- Security Classification

---


## 8.4 Permission Matrix

יש להגדיר מטריצה מפורשת של:

**Role × Object × Action**

לדוגמה:

| Role | Audit | Finding | Action | Report | User Mgmt |
|---|---|---|---|---|---|
| System Admin | Full | Full | Full | Full | Full |
| Audit Programme Manager | Create/Edit/Assign | View/Monitor | View | Approve/View | No |
| Lead Auditor | Edit/Execute | Create/Edit | Create/Edit | Draft/Submit | No |
| Auditor | Execute | Create/Edit | Create/Edit | Contribute | No |
| Auditee Representative | View Relevant | Respond | Update Assigned | View | No |
| Finding Owner | View | Update Assigned | Update Assigned | View | No |
| Approver | View | Verify/Close | Verify | Approve | No |
| Viewer | Read | Read | Read | Read | No |

> המטריצה לעיל היא דוגמת אפיון בלבד; יש לקבע אותה בהתאם למבנה הארגוני בפועל.

---

## 8.5 Segregation of Duties

יש למנוע מצבים שבהם אותו משתמש:

- יוצר וגם מאשר מבדק ללא בקרה
- סוגר ממצא שהוא עצמו Owner שלו ללא אימות בלתי תלוי
- משנה קריטריון לאחר תחילת מבדק ללא Audit Trail
- מוחק ראיות לאחר שימוש בהן לסגירת ממצא

---

## 8.6 Information Security & Access Control Architecture

אבטחת מידע היא דרישת Core ולא הרחבה מאוחרת.

### Authentication

המערכת צריכה לתמוך ב:

- SSO ארגוני
- MFA לפי מדיניות הארגון
- Identity Provider ארגוני
- Session Timeout
- Account Lockout / Risk Controls

### Authorization

- RBAC
- ABAC לפי צורך
- Row-Level Security
- הרשאות לפי יחידה / פרויקט / ספק / Audit
- הרשאות לפי Security Classification
- Least Privilege
- Segregation of Duties

### Data Protection

- Encryption in Transit
- Encryption at Rest
- הגנת קבצים מצורפים
- מניעת גישה ישירה ל-Storage
- Signed / Controlled URLs לקבצים
- Data Retention Policy
- Secure Deletion בהתאם למדיניות

### Audit & Monitoring

יש לשמור:

- Login Events
- Failed Login Events
- Permission Changes
- Record Changes
- Export Events
- Download Events
- Closure/Reopen Events
- Administrative Actions

המערכת צריכה לאפשר:

- Security Logging
- Monitoring
- Alerting
- Audit Trail בלתי ניתן לשינוי על ידי משתמש רגיל

### מידע רגיש וסיווג

לכל אובייקט רלוונטי ניתן להוסיף:

- Security Classification
- Need-to-Know
- Restricted Audience
- Export Restriction
- Download Restriction

דוגמאות:

- מבדק פנימי רגיל
- מבדק ספק מסווג
- מבדק פרויקט
- ממצא רגיש
- ראיה מוגבלת

### Export & Download Control

יש להגדיר במפורש:

- מי רשאי להפיק PDF
- מי רשאי להוריד Attachments
- האם ניתן להדפיס
- האם נדרש Watermark
- האם נדרש תיעוד Export
- האם קבצים ניתנים לשיתוף מחוץ למערכת

### Backup / Recovery

- גיבוי
- שחזור
- RPO
- RTO
- בדיקות שחזור תקופתיות

### Deployment

נדרש לקבוע בהמשך:

- Cloud
- Private Cloud
- On-Prem
- Air-Gapped / Closed Network

בהתאם למדיניות הארגון ולרגישות המידע.

---

# 9. MVP — פיצ'רי ליבה

ה-MVP צריך להוכיח:

> ניתן לנהל מבדק מקצה לקצה במערכת אחת.

## MVP-1 — Audit Lifecycle

- יצירת מבדק
- שיוך לתוכנית
- סטטוסים
- מעברי מצב
- היסטוריית שינויים

---

## MVP-2 — Audit Setup

- Objective
- Scope
- Criteria
- Auditee
- Lead Auditor
- Team
- Dates

---

## MVP-3 — Checklist / Criteria

- יצירת שאלות
- שיוך לקריטריונים
- תיעוד תשובות
- תיעוד Evidence

---

## MVP-4 — Findings, Follow-up & Effectiveness

- פתיחת Finding
- Owner
- Due Date
- Immediate Correction
- Root Cause
- Corrective Action
- Implementation Evidence
- Verification
- Effectiveness Check לפי צורך
- Overdue / Aging
- Reminder / Escalation
- Reopen
- Closure

---

## MVP-5 — Report, Closure & Controlled Access

- דוח מבדק
- Summary
- Findings
- סטטוס
- Approval
- Closure Gate
- Role-based access
- Audit Trail
- Controlled export
- Security classification בסיסי

---

# 10. מה לא להכניס ל-MVP

בכוונה נדחה:

- AI
- RAG
- Risk Scoring Engine
- Predictive Planning
- Auditor Auto-Matching
- Full CAPA
- Offline Mobile
- Supplier Portal
- OASIS Integration
- SAP Integration
- PLM Integration
- Advanced BI
- Automated Benchmarking
- Voice
- OCR
- Automated Classification

---

# 11. מה כן צריך להכין ארכיטקטונית כבר עכשיו

למרות שאינו ב-MVP:

## Audit Universe

המערכת צריכה להיות מסוגלת בעתיד לדעת מה ניתן לבדיקה:

- Processes
- Suppliers
- Projects
- Products
- Units
- Sites
- Standards

---

## Auditor Competence

יש להשאיר יכולת עתידית להתאמת מבקרים לפי:

- Qualification
- Independence
- Experience
- Availability
- Standard
- Audit Type

---

## Versioning

חובה לתמוך בעתיד בגרסאות עבור:

- Standards
- Checklists
- Questions
- Criteria

---

## Integration Layer

API Layer נפרד עבור:

- SAP
- PLM
- HR
- SharePoint
- QMS
- OASIS

---

## Security Architecture

יש להכין מראש:

- SSO / MFA integration
- RBAC / ABAC model
- Security Classification
- Audit Logging
- Encryption
- Export controls
- Attachment controls
- Backup / Recovery
- Deployment architecture

# 12. SWOT מאוחד

## Strengths

- Lifecycle מקצועי
- Closed Loop
- Traceability
- התאמה לעולם איכות
- התאמה עתידית לתעופה / ביטחון
- אפשרות לצמוח ל-Audit Intelligence

---

## Weaknesses

- Data Model מורכב
- נדרש Master Data איכותי
- תלות בהגדרת Process נכונה
- סכנת Customization יתר
- צורך באימוץ משתמשים

---

## Opportunities

- Risk-Based Audit Planning
- חיבור למערכות ארגוניות
- AI/RAG
- Continuous Assurance
- Supplier Audit Intelligence
- Cross-Audit Analytics

---

## Threats

- מערכות קיימות ובשלות
- מעבר משתמשים חזרה ל-Excel
- אבטחת מידע
- Integration Complexity
- Vendor Lock-in
- רישוי תוכן תקני

---

# 13. אתגרים טכניים עיקריים

## 13.1 Data Model

האתגר המרכזי.

---

## 13.2 Workflow Engine

לא לבנות סטטוסים קשיחים מדי.

---

## 13.3 Version Control

מבדק חייב לשמר את הקריטריונים שהיו תקפים במועד הביצוע.

---

## 13.4 RBAC / ABAC

ייתכן שרק RBAC לא יספיק.

---

## 13.5 Audit Trail

כל שינוי משמעותי חייב להיות מתועד.

---

## 13.6 Evidence Management

ראיה חייבת להיות ישות עם Traceability.

---

## 13.7 Reporting

יש להפריד בין:

- Live Data
- Snapshot Report

---

# 14. Benchmark — מסקנות ממערכות קיימות

## OASIS

מה ללמוד:

- סטנדרטיזציה
- סטטוסים
- מבקרים
- תוצאות
- NCR
- Traceability

לא להעתיק:

- מבנה מערכת הסמכה חיצונית

---

## Intact

מה ללמוד:

- Competency-aware planning
- Checklist Engine
- Evidence
- Findings
- Review
- BI
- Mobile / Offline

---

## ActionBase

מה ללמוד:

- Workflow
- Responsibility
- Follow-up
- Task ownership

---

## Intelex / ETQ

מה ללמוד:

- Audit + Finding + CAPA
- Reporting
- Workflow
- Analytics

---

# 15. עקרונות UX

המערכת חייבת להיות פשוטה למבקר.

מסך Audit צריך להציג:

- Status
- Scope
- Team
- Criteria
- Checklist
- Evidence
- Findings
- Actions
- Report

בלי צורך לנווט בין מערכות נפרדות.

---

# 16. KPI ל-MVP

- % מבדקים שבוצעו בזמן
- % Findings באיחור
- זמן ממוצע לסגירת Finding
- % ממצאים שעברו Verification במועד
- % ממצאים שעברו Effectiveness Check במועד
- % ממצאים שנפתחו מחדש
- % ממצאים חוזרים
- זמן ממוצע ממבדק לדוח
- % מבדקים שנסגרו ללא כלי חיצוני
- % Evidence המקושר לקריטריון
- % Findings עם Owner ו-Due Date
- % פעולות באיחור

---

# 17. סדר העבודה המומלץ

המשך האפיון צריך להתבצע בסדר הבא:

## שלב 1 — Lifecycle

לקבע:

- States
- Transitions
- Permissions
- Preconditions

---

## שלב 2 — Data Model

להגדיר:

- Entities
- Fields
- Relationships
- Versioning

---

## שלב 3 — Finding Model

להגדיר:

- Classification
- Workflow
- Actions
- Verification
- Closure

---

## שלב 4 — Roles, Permissions & Information Security

לבנות:

- Role Matrix
- Permission Matrix
- Data Visibility
- Approval Rights
- Segregation of Duties
- Authentication
- Security Classification
- Export / Download Controls
- Audit Logging

---

## שלב 5 — MVP User Stories

לכל פעולה:

- User
- Need
- Reason
- Acceptance Criteria

---

## שלב 6 — Prototype

רק לאחר השלמת 1–5.

---

# 18. החלטות שעדיין אסור לקבע

עדיין לא הוחלט:

- האם הנבדק ממלא שאלון
- האם קיימים שלושה סוגי שאלות בלבד
- האם יש ציון
- האם כל מבדק דורש CAPA
- האם ספקים ייכנסו למערכת ישירות
- האם המערכת תהיה Cloud או On-Prem
- האם תידרש אפליקציה
- האם המבקר וה-Editor הם אותו Role

---

# 19. שאלות פתוחות

1. מהם סוגי המבדקים שיופעלו בגרסה הראשונה?
2. מי יזין בפועל את התשובות?
3. מי רשאי לפתוח Finding?
4. מי רשאי לסגור Finding?
5. מי רשאי לבצע Verification?
6. מי רשאי לבצע Effectiveness Check?
7. מי מאשר דוח?
8. מה ההבדל אצלך בין "הסתיים" ל"סגור"?
9. האם Root Cause נדרש לכל ממצא או רק לפי סיווג?
10. אילו ממצאים מחייבים Effectiveness Check?
11. מהו פרק הזמן המינימלי לפני בדיקת אפקטיביות?
12. האם Supplier Users ייכנסו למערכת?
13. האם יש סיווג מידע?
14. האם נדרש On-Prem / רשת סגורה?
15. האם נדרש SSO / MFA?
16. האם יש מגבלות על Export / Print / Download?
17. האם יש מערכת ארגונית קיימת לניהול NCR/CAPA?

---

# 20. הגדרת מוצר סופית לגרסה הנוכחית

## MVP

> מערכת לניהול מחזור חיי מבדק מלא, הכוללת תכנון, קריטריונים, ביצוע, ראיות, ממצאים, פעולות, מעקב, Verification, בדיקת אפקטיביות, דוח וסגירה מבוקרת — תחת מודל הרשאות ואבטחת מידע ארגוני.

## Target Architecture

> Enterprise Audit Management Platform מבוססת Traceability, Risk, Competence ו-Analytics.

## Long-Term Vision

> Audit Intelligence Platform שמחברת מידע ממבדקים, ספקים, תהליכים, מוצרים, פרויקטים ומערכות ארגוניות ומסייעת לתכנן את פעילות האיכות על בסיס סיכון ונתונים.
