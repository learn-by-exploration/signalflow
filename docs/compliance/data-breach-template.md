# Data Breach Notification Template

> **Regulatory basis**: DPDPA 2023 §8(6) — 72-hour notification to Data Protection Board of India
> **Status**: Template — to be used in the event of a data breach
> **Last reviewed**: 24 March 2026

---

## 1. Notification to Data Protection Board of India

**Required within 72 hours of breach discovery.**

### Template

**Subject:** Data Breach Notification — SignalFlow AI

Respected Sir/Madam,

This notice is submitted pursuant to Section 8(6) of the Digital Personal Data Protection Act, 2023.

**1. Nature of the breach:**
[Describe the nature of the breach — unauthorized access, data leak, system compromise, etc.]

**2. Date and time of breach discovery:**
[YYYY-MM-DD HH:MM IST]

**3. Estimated date/time breach occurred:**
[YYYY-MM-DD HH:MM IST, or "Under investigation"]

**4. Categories of personal data affected:**
- [ ] Email addresses
- [ ] Telegram chat IDs
- [ ] Trade/portfolio data
- [ ] Alert preferences / Watchlists
- [ ] Other: [specify]

**5. Estimated number of data principals affected:**
[Number or range]

**6. Likely consequences of the breach:**
[Describe potential harm — identity theft, financial loss, privacy violation, etc.]

**7. Measures taken to address the breach:**
- [Immediate containment steps]
- [Notification to affected users]
- [Technical remediation]

**8. Measures taken to mitigate adverse effects:**
- [Steps to protect affected users]
- [Monitoring put in place]

**9. Contact person:**
Name: [Grievance Officer Name]
Email: privacy@signalflow.ai

Yours sincerely,
[Name], [Title]
SignalFlow AI

---

## 2. Notification to Affected Users

**Send via:** Email and Telegram (both channels)

### Template

**Subject:** Important Security Notice — SignalFlow AI

Dear User,

We are writing to inform you of a security incident affecting your SignalFlow AI account.

**What happened:**
[Brief, clear description of the incident]

**What data was affected:**
[List specific data types affected for this user]

**When it happened:**
[Date/time or approximate period]

**What we are doing:**
- [Containment measures taken]
- [Investigation steps]
- [Security improvements being implemented]

**What you should do:**
- If you use the same password elsewhere, change it immediately
- Be alert for suspicious communications claiming to be from SignalFlow AI
- We will never ask for your password via email or Telegram

**Questions?**
Contact our Grievance Officer at privacy@signalflow.ai

We sincerely apologize for this incident and are committed to protecting your data.

Regards,
The SignalFlow AI Team

---

## 3. Internal Incident Response Checklist

### Immediate (0-4 hours)
- [ ] Contain the breach (revoke access, rotate credentials)
- [ ] Assess scope (what data, how many users, how it happened)
- [ ] Document everything (timeline, actions, decisions)
- [ ] Notify engineering lead
- [ ] Begin forensic investigation

### Short-term (4-72 hours)
- [ ] Notify Data Protection Board of India (within 72 hours)
- [ ] Notify affected users via email and Telegram
- [ ] Rotate all API keys and secrets (Anthropic, Telegram, database)
- [ ] Review access logs for the breach period
- [ ] Patch vulnerability that enabled the breach

### Follow-up (1-4 weeks)
- [ ] Complete forensic investigation
- [ ] Implement additional security measures
- [ ] Update security documentation
- [ ] Conduct internal review / post-mortem
- [ ] File follow-up report with DPB if required

---

## 4. Escalation Contacts

| Role | Contact | When to Notify |
|------|---------|---------------|
| Grievance Officer | privacy@signalflow.ai | Immediately |
| Data Protection Board of India | https://www.meity.gov.in | Within 72 hours |
| Hosting Provider (Railway) | Railway support | If infrastructure compromised |
| Anthropic | Anthropic support | If API key compromised |

---

*This template should be reviewed annually and updated after any security incident.*
