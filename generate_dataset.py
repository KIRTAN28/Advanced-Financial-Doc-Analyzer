"""
Dataset Generator — Realistic Multi-Company Corporate Filings
=============================================================
Generates a FLAT folder of mixed documents for multiple companies,
matching the real SH-7 / PAS-3 / MOA / Board Resolution structure
from the Assignment File reference docs.

Output: dataset/ folder with all files at top level (no sub-grouping)
to test the pipeline's automatic classification and grouping.
"""

import os
from pathlib import Path

DATASET_DIR = Path("dataset")

# ──────────────────────────────────────────────────────────────
# Company 1: NEXUS BRIGHTLEARN SOLUTIONS PRIVATE LIMITED
# ──────────────────────────────────────────────────────────────

COMPANY_1 = {
    "name": "NEXUS BRIGHTLEARN SOLUTIONS PRIVATE LIMITED",
    "short": "Nexus",
    "cin": "U85123DL2018PTC312456",
    "address": "KRISHNA TOWER PLOT NO-45 SECTOR-12 DWARKA NEW DELHI New Delhi Delhi 110075",
    "director": "ARUN VIKRAM SETHI",
    "din": "08745632",
    "email": "arunsethi@outlook.com",
    "incorp_date": "05/02/2018",
    "incorp_capital": "1,50,000",
    "incorp_shares": "15,000",
    "face_value": "10",
}

COMPANY_1_EVENTS = [
    {
        "id": "event_1",
        "date": "22/03/2018",
        "date_formatted": "March 22, 2018",
        "meeting_type": "EGM",
        "old_cap": "1,50,000",
        "new_cap": "3,00,000",
        "diff_cap": "1,50,000",
        "old_eq": "15,000",
        "new_eq": "30,000",
        "diff_eq": "15,000",
        "old_pref": "0",
        "new_pref": "0",
    },
    {
        "id": "event_2",
        "date": "15/09/2020",
        "date_formatted": "September 15, 2020",
        "meeting_type": "EGM",
        "old_cap": "3,00,000",
        "new_cap": "10,00,000",
        "diff_cap": "7,00,000",
        "old_eq": "30,000",
        "new_eq": "1,00,000",
        "diff_eq": "70,000",
        "old_pref": "0",
        "new_pref": "0",
    },
    {
        "id": "event_3",
        "date": "10/03/2023",
        "date_formatted": "March 10, 2023",
        "meeting_type": "AGM",
        "old_cap": "10,00,000",
        "new_cap": "1,00,00,000",
        "diff_cap": "90,00,000",
        "old_eq": "1,00,000",
        "new_eq": "10,00,000",
        "diff_eq": "9,00,000",
        "old_pref": "0",
        "new_pref": "0",
    },
    {
        "id": "event_4",
        "date": "29/09/2025",
        "date_formatted": "September 29, 2025",
        "meeting_type": "AGM",
        "old_cap": "1,00,00,000",
        "new_cap": "11,00,00,000",
        "diff_cap": "10,00,00,000",
        "old_eq": "10,00,000",
        "new_eq": "1,09,90,000",
        "diff_eq": "99,90,000",
        "old_pref": "0",
        "new_pref": "10,000",
    },
]

# ──────────────────────────────────────────────────────────────
# Company 2: PINNACLE INFRATECH SOLUTIONS PRIVATE LIMITED
# ──────────────────────────────────────────────────────────────

COMPANY_2 = {
    "name": "PINNACLE INFRATECH SOLUTIONS PRIVATE LIMITED",
    "short": "Pinnacle",
    "cin": "U74999MH2019PTC345678",
    "address": "301 TOWER-B TECHNO PARK GOREGAON EAST MUMBAI Maharashtra 400063",
    "director": "RAHUL KUMAR MEHRA",
    "din": "09123456",
    "email": "rahulmehra@pinnacleinfra.com",
    "incorp_date": "12/06/2019",
    "incorp_capital": "1,00,000",
    "incorp_shares": "10,000",
    "face_value": "10",
}

COMPANY_2_EVENTS = [
    {
        "id": "event_1",
        "date": "18/11/2020",
        "date_formatted": "November 18, 2020",
        "meeting_type": "EGM",
        "old_cap": "1,00,000",
        "new_cap": "5,00,000",
        "diff_cap": "4,00,000",
        "old_eq": "10,000",
        "new_eq": "50,000",
        "diff_eq": "40,000",
        "old_pref": "0",
        "new_pref": "0",
    },
    {
        "id": "event_2",
        "date": "05/08/2022",
        "date_formatted": "August 5, 2022",
        "meeting_type": "EGM",
        "old_cap": "5,00,000",
        "new_cap": "25,00,000",
        "diff_cap": "20,00,000",
        "old_eq": "50,000",
        "new_eq": "2,50,000",
        "diff_eq": "2,00,000",
        "old_pref": "0",
        "new_pref": "0",
    },
    {
        "id": "event_3",
        "date": "20/03/2024",
        "date_formatted": "March 20, 2024",
        "meeting_type": "AGM",
        "old_cap": "25,00,000",
        "new_cap": "5,00,00,000",
        "diff_cap": "4,75,00,000",
        "old_eq": "2,50,000",
        "new_eq": "50,00,000",
        "diff_eq": "47,50,000",
        "old_pref": "0",
        "new_pref": "0",
    },
]


# ──────────────────────────────────────────────────────────────
# Document Templates (matching real SH-7 / Board Res structure)
# ──────────────────────────────────────────────────────────────

def gen_sh7(company, event):
    return f"""# FORM NO. SH-7

**Notice to Registrar of any alteration of share capital**

[Pursuant to section 64(1) of the Companies Act, 2013 and pursuant to rule 63 of the Companies Rules, 2014]

**Form language** ⊙ English ○ Hindi

1.(a)* Corporate identity number (CIN) of the company | {company['cin']} | Pre-fill

2.(a) Name of the company | {company['name']}

(b) Address of the registered office of the company | {company['address']}

(c) * email Id of the company | {company['email']}

3. * Purpose of the form
⊙ Increase in share capital independently by company

4. In accordance with section 61(1) of the Companies Act, 2013, that by ⊙ Ordinary ○ Special resolution at
the meeting of the members of the company held on | {event['date']} | (DD/MM/YYYY)

(a)(i) The authorised share capital of the company has been increased from

| | |
|---|---|
| Existing (in Rs.) | {event['old_cap']} |
| Revised (in Rs.) | {event['new_cap']} |
| Difference (addition) (in Rs.) | {event['diff_cap']} |

6. The additional capital (taking into consideration the addition above) is divided as follows

(a) Number of equity shares | {event['diff_eq']} | Total amount of equity shares (in Rs.) | {event['diff_cap']}
(b) Number of preference shares | {event.get('new_pref', '0')} | Total amount of preference shares |

9. Revised capital structure after taking into consideration the changes

(a) Authorised capital of the company (in Rs.) {event['new_cap']}

Break up of Authorised capital

| | | | |
|---|---|---|---|
| Number of equity shares | {event['new_eq']} | Total amount of equity shares (in Rs.) | {event['new_cap']} |
| Nominal amount per equity share | {company['face_value']} | | |
| Number of preference shares | {event.get('new_pref', '0')} | Total amount of preference shares (in Rs.) | 0 |
| Nominal amount per preference share | {company['face_value']} | | |

**Declaration**
I *{company['director']}, Director of the company declare that all the requirements of the Companies Act, 2013 have been complied with.

*DIN: {company['din']}
eForm filing date {event['date']} (DD/MM/YYYY)
"""


def gen_board_meeting(company, event):
    return f"""# {company['name']}

## CERTIFIED TRUE COPY OF RESOLUTION PASSED IN THE MEETING OF THE BOARD OF DIRECTORS OF {company['name']} HAVING ITS REGISTERED OFFICE AT {company['address']} HELD ON {event['date']}

## INCREASE IN AUTHORISED SHARE CAPITAL & ALTERATION IN THE CAPITAL CLAUSE OF MEMORANDUM OF ASSOCIATION

1. "RESOLVED THAT pursuant to the provisions of Section 61 and 64 and other applicable provisions, if any, of the Companies Act, 2013 (including any amendment thereto or re-enactment thereof) and the rules framed there under, the consent of the Board of Directors of the Company be and is hereby accorded, subject to the approvals of shareholders in the General meeting, to increase the Authorized Share Capital of the Company from existing Rs. {event['old_cap']}/- divided into {event['old_eq']} Equity Shares of Rs. {company['face_value']}/- each to Rs. {event['new_cap']}/- divided into {event['new_eq']} Equity Shares of Rs. {company['face_value']}/- each.

2. RESOLVED FURTHER THAT pursuant to the provisions of Section 13, 61 and 64, the consent of the Board is hereby accorded for substituting Clause V of the Memorandum of Association with the following clause:

V. The Authorised Share Capital of the Company is Rs. {event['new_cap']}/- divided into {event['new_eq']} Equity Shares of Rs. {company['face_value']}/- each."

3. FURTHER RESOLVED THAT Mr. {company['director']}, Director of the Company be and is hereby authorized to sign and file the necessary documents with the concerned authorities including Registrar of Companies.

**BY ORDER OF THE BOARD**

Date: {event['date']}

**{company['director']}
(DIRECTOR)
DIN: {company['din']}**

CIN: {company['cin']}
"""


def gen_notice(company, event):
    return f"""# {company['name']}

NOTICE IS HEREBY GIVEN THAT THE **{event['meeting_type']}** OF THE MEMBERS OF **{company['name']}** WILL BE HELD ON {event['date']} AT ITS REGISTERED OFFICE AT {company['address']} TO TRANSACT THE FOLLOWING BUSINESS:

## SPECIAL BUSINESS:

### ITEM NO. 1

**RESOLVED THAT** pursuant to Sections 61, 64 and other applicable provisions of the Companies Act, 2013, the consent of the board of directors be hereby accorded to increase the Authorized Share Capital of the Company from Rs. {event['old_cap']}/- divided into {event['old_eq']} Equity Shares of Rs. {company['face_value']}/- each to Rs. {event['new_cap']}/- divided into {event['new_eq']} Equity Shares of Rs. {company['face_value']}/- each.

### ITEM NO. 2

**RESOLVED THAT** Clause V of the Memorandum of Association be substituted with:

V. The Authorised Share Capital of the Company is Rs. {event['new_cap']}/- divided into {event['new_eq']} Equity Shares of Rs. {company['face_value']}/- each.

**BY ORDER OF THE BOARD**

Date: {event['date']}

**{company['director']}
(DIRECTOR)
DIN: {company['din']}**

CIN: {company['cin']}
"""


def gen_meeting_minutes(company, event):
    return f"""# {company['name']}

**CERTIFIED TRUE COPY OF THE RESOLUTION PASSED AT THE {event['meeting_type']} OF {company['name']} HAVING ITS REGISTERED OFFICE AT {company['address']} HELD ON {event['date']}**

## INCREASE IN AUTHORISED SHARE CAPITAL

The Chairman informed the members that it is proposed to increase the Authorized Share Capital of the Company from Rs. {event['old_cap']}/- divided into {event['old_eq']} Equity Shares of Rs. {company['face_value']}/- each to Rs. {event['new_cap']}/- divided into {event['new_eq']} Equity Shares of Rs. {company['face_value']}/- each, to accommodate future business requirements.

The members unanimously passed the resolution to increase the share capital and to alter Clause V of the Memorandum of Association accordingly.

**BY ORDER OF THE BOARD**

Date: {event['date']}

**{company['director']}
(DIRECTOR)
DIN: {company['din']}**

CIN: {company['cin']}
"""


def gen_moa(company):
    return f"""THE COMPANIES ACT, 2013
(COMPANY LIMITED BY SHARES)
MEMORANDUM OF ASSOCIATION
OF
{company['name']}

I. The Name of the Company is {company['name']}.
II. The Registered Office of the Company will be situated at {company['address']}.
III. The objects for which the Company is established are:-
(A) THE MAIN OBJECTS TO BE PURSUED BY THE COMPANY ON ITS INCORPORATION ARE:-
1. To carry on the business as described in the main objects clause.

IV. The Liability of the members is Limited.

V. The Authorised Share Capital of the Company is Rs. {company['incorp_capital']}/- divided into {company['incorp_shares']} Equity Shares of Rs. {company['face_value']}/- each.

DATE: {company['incorp_date']}
CIN: {company['cin']}
"""


def gen_pas3(company, event_date, shares_allotted, premium, allottees):
    return f"""# FORM NO. PAS-3 Return of Allotment

[Pursuant to section 39(4) and 42(9) of the Companies Act, 2013]

1.(a) *Corporate Identity Number (CIN) of company | {company['cin']}

2.(a) Name of the company | {company['name']}

(b) Address of the Registered office | {company['address']}

3. Securities allotted payable in cash

*Number of allotments | 1

1 (i)* Date of allotment | {event_date} | (DD/MM/YYYY)

| Particulars | | Equity shares without Differential rights |
|---|---|---|
| Number of securities allotted | | {shares_allotted} |
| Nominal amount per security | (in Rs.) | {company['face_value']} |
| Total nominal amount | (in Rs.) | {int(shares_allotted.replace(',', '')) * int(company['face_value'])} |
| Premium amount per security | (in Rs.) | {premium} |

7.* Capital structure after allotment:

| Particulars | Authorized capital | Issued capital |
|---|---|---|
| Number of equity shares | {company['incorp_shares']} | {shares_allotted} |

## Declaration
I am authorized by the Board of Directors of the Company.

*{company['director']}
(DIRECTOR)
DIN: {company['din']}

CIN: {company['cin']}
"""


def gen_board_allotment(company, event_date, shares, allottees):
    allottee_table = ""
    for a in allottees:
        allottee_table += f"| {a['name']} | {a['shares']} | {a['folio']} |\n"

    return f"""{company['name']}
CERTIFIED TRUE COPY OF THE RESOLUTION PASSED AT THE MEETING OF THE BOARD OF DIRECTORS OF {company['name']} HELD ON {event_date}

ALLOTMENT OF {shares} EQUITY SHARES OF THE COMPANY:

"RESOLVED THAT pursuant to Section 62(1) of the Companies Act, 2013, the approval of the Board be and is hereby accorded to the allotment of {shares} equity shares of face value INR {company['face_value']} each to the below mentioned Investors:

| Name of the Allottee | No. Equity Shares | Folio No. |
|---|---|---|
{allottee_table}
RESOLVED FURTHER THAT the said Equity Shares shall rank pari passu with the existing equity shares.

For {company['name']}
{company['director']}
Director DIN - {company['din']}
CIN: {company['cin']}
"""


def gen_list_allottees(company, event_date, allottees, premium):
    rows = ""
    for i, a in enumerate(allottees, 1):
        rows += f"| {i}. | {a['name']} | {a['address']} | Indian | {a['shares']} | {int(a['shares'].replace(',','')) * (int(company['face_value']) + int(premium.replace(',','')))} | Nil |\n"

    return f"""{company['name']}
List of Allottees

Table A
| Name of the Company | {company['name']} |
|---|---|
| Date of the allotment | {event_date} |
| Type of share allotted | Equity Shares |
| Nominal value per share | Rs. {company['face_value']}/- each |
| Premium amount per share | Rs. {premium} |
| Total number of allottees | {len(allottees)} |

Table B (List of allottees)
| Sr.no. | Name | Address | Nationality | No. of shares | Total amount paid (Rs.) | Outstanding |
|---|---|---|---|---|---|---|
{rows}
CIN: {company['cin']}
For {company['name']}
{company['director']}
Director DIN - {company['din']}
"""


def main():
    # Clean and recreate dataset directory
    if DATASET_DIR.exists():
        import shutil
        shutil.rmtree(DATASET_DIR)
    DATASET_DIR.mkdir()

    # ── Company 1: Nexus Brightlearn ──
    # MOA
    with open(DATASET_DIR / f"Nexus_MOA.md", "w", encoding="utf-8") as f:
        f.write(gen_moa(COMPANY_1))

    # 4 SH-7 events with 3 attachments each
    for ev in COMPANY_1_EVENTS:
        prefix = f"Nexus_{ev['id']}"
        with open(DATASET_DIR / f"{prefix}_SH7.md", "w", encoding="utf-8") as f:
            f.write(gen_sh7(COMPANY_1, ev))
        with open(DATASET_DIR / f"{prefix}_Board_Meeting.md", "w", encoding="utf-8") as f:
            f.write(gen_board_meeting(COMPANY_1, ev))
        with open(DATASET_DIR / f"{prefix}_Notice_{ev['meeting_type']}.md", "w", encoding="utf-8") as f:
            f.write(gen_notice(COMPANY_1, ev))
        with open(DATASET_DIR / f"{prefix}_{ev['meeting_type']}_Minutes.md", "w", encoding="utf-8") as f:
            f.write(gen_meeting_minutes(COMPANY_1, ev))

    # PAS-3 for Nexus (allotment event)
    nexus_allottees = [
        {"name": "Mr. Rohit Sharma", "shares": "192", "folio": "8", "address": "12/45 Sunrise Apartments, Sector-15, Rohini, New Delhi 110085"},
        {"name": "Mr. Suresh Sharma", "shares": "192", "folio": "9", "address": "12/45 Sunrise Apartments, Sector-15, Rohini, New Delhi 110085"},
        {"name": "Sunrise Engineering Works Pvt. Ltd", "shares": "576", "folio": "10", "address": "302 Lakshmi Tower, Ring Road, Lajpat Nagar, New Delhi 110024"},
    ]
    with open(DATASET_DIR / "Nexus_PAS3_Form.md", "w", encoding="utf-8") as f:
        f.write(gen_pas3(COMPANY_1, "15/05/2019", "960", "7,850", nexus_allottees))
    with open(DATASET_DIR / "Nexus_PAS3_Board_Resolution_Allotment.md", "w", encoding="utf-8") as f:
        f.write(gen_board_allotment(COMPANY_1, "15/05/2019", "960", nexus_allottees))
    with open(DATASET_DIR / "Nexus_PAS3_List_of_Allottees.md", "w", encoding="utf-8") as f:
        f.write(gen_list_allottees(COMPANY_1, "15/05/2019", nexus_allottees, "7,850"))

    # ── Company 2: Pinnacle Infratech ──
    # MOA
    with open(DATASET_DIR / f"Pinnacle_MOA.md", "w", encoding="utf-8") as f:
        f.write(gen_moa(COMPANY_2))

    # 3 SH-7 events
    for ev in COMPANY_2_EVENTS:
        prefix = f"Pinnacle_{ev['id']}"
        with open(DATASET_DIR / f"{prefix}_SH7.md", "w", encoding="utf-8") as f:
            f.write(gen_sh7(COMPANY_2, ev))
        with open(DATASET_DIR / f"{prefix}_Board_Meeting.md", "w", encoding="utf-8") as f:
            f.write(gen_board_meeting(COMPANY_2, ev))
        with open(DATASET_DIR / f"{prefix}_Notice_{ev['meeting_type']}.md", "w", encoding="utf-8") as f:
            f.write(gen_notice(COMPANY_2, ev))
        with open(DATASET_DIR / f"{prefix}_{ev['meeting_type']}_Minutes.md", "w", encoding="utf-8") as f:
            f.write(gen_meeting_minutes(COMPANY_2, ev))

    # PAS-3 for Pinnacle
    pinnacle_allottees = [
        {"name": "Mr. Vikash Gupta", "shares": "500", "folio": "5", "address": "A-12 Green Park, Andheri West, Mumbai 400058"},
        {"name": "BlueStar Ventures LLP", "shares": "1,500", "folio": "6", "address": "Tower C, Bandra Kurla Complex, Mumbai 400051"},
    ]
    with open(DATASET_DIR / "Pinnacle_PAS3_Form.md", "w", encoding="utf-8") as f:
        f.write(gen_pas3(COMPANY_2, "20/01/2021", "2,000", "5,000", pinnacle_allottees))
    with open(DATASET_DIR / "Pinnacle_PAS3_Board_Resolution_Allotment.md", "w", encoding="utf-8") as f:
        f.write(gen_board_allotment(COMPANY_2, "20/01/2021", "2,000", pinnacle_allottees))
    with open(DATASET_DIR / "Pinnacle_PAS3_List_of_Allottees.md", "w", encoding="utf-8") as f:
        f.write(gen_list_allottees(COMPANY_2, "20/01/2021", pinnacle_allottees, "5,000"))

    # Count files
    files = list(DATASET_DIR.glob("*.md"))
    print(f"Dataset generated successfully: {len(files)} documents in {DATASET_DIR}/")
    for f in sorted(files):
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
