# Guidelines + PubMed Eval Results

Run: `2026-07-27T20:18:57.077066+00:00`

Passed: `5/10`

| Case | Pass | Guidelines | PubMed | Cited | Notes |
|---|---:|---:|---:|---|---|
| severe_malaria_management | yes | 4 | 3 | [1], [2], [4] | ok |
| uncomplicated_malaria_adult | yes | 4 | 3 | [1], [2], [4] | ok |
| breast_tumour_oncovin | no | 4 | 3 | [1], [2], [3], [4] | required_terms_present |
| sciatica_management | yes | 4 | 3 | [1], [2], [4] | ok |
| hypertension_pregnancy | no | 4 | 3 | - | required_terms_present |
| type_2_diabetes | yes | 4 | 3 | [1], [3] | ok |
| child_pneumonia | no | 2 | 3 | [1], [2] | required_terms_present |
| acute_asthma | yes | 4 | 3 | [1], [2] | ok |
| uti_pregnancy | no | 4 | 3 | [5], [6], [7] | required_terms_present |
| irrelevant_crypto | no | 4 | 3 | - | required_terms_present |

## Case Details

### severe_malaria_management

Question: How should severe malaria be managed?

Checks: `{"answered": true, "citations_valid": true, "expected_sources_present": true, "forbidden_terms_absent": true, "pubmed_retrieved_when_preferred": true, "required_terms_present": true}`

PubMed PMIDs: `36203155, 35916842, 35959375`

Answer:

Severe malaria should be treated as a **medical emergency** with **immediate parenteral antimalarial therapy** and supportive care, aiming to **eradicate parasitaemia and prevent progression to death** [1,2].

## 1) Start treatment immediately (do not delay)
- **Parasitological confirmation is recommended for all suspected malaria**, but **microscopy/RDT confirmation should not delay appropriate treatment if there is clinical suspicion of severe malaria** [1,2].
- **Parenteral artesunate is the drug of choice**, and **treatment should be started without delay** [1].

## 2) First-line drug: Parenteral artesunate (adult/child dosing)
Start **IV or IM artesunate**:
- **Adults and children > 20 kg:** **2.4 mg/kg** on admission (**time 0**), then **at 12 hours and 24 hours**, then **once daily** [1].
  - **There is no upper limit to the total dose of artesunate** [1].
- **Children ≤ 20 kg:** **3 mg/kg** on admission (**time 0**), then **at 12 hours and 24 hours**, then **once daily** [1].

## 3) If IV artesunate is not available
- If parenteral artesunate is not available, **commence another effective parenteral antimalarial** (guideline lists **parenteral artemether or quinine as alternatives**) [1].

## 4) Pre-referral treatment (if severe malaria case needs transfer)
To mitigate poor outcomes, **pre-referral treatment should be offered** once severe disease is suspected [1].
Recommended options (in order of preference) include [1]:
- **Rectal artesunate** (single dose)
- **Artesunate IM**
- **Artemether IM**
- **Quinine IM**

Pre-referral dosing [1]:
- **IM artesunate:**
  - **3 mg/kg** (children <6 years or <20 kg)
  - **2.4 mg/kg** (older children and adults)
- **Rectal artesunate:** **10 mg/kg** single dose
- **IM artemether:** **3.2 mg/kg**
- **IM quinine:** **10 mg/kg**

## 5) Identify severity promptly
Severe malaria features include (examples) [2]:
- **Impaired consciousness/unrousable coma**, **prostration**
- **Respiratory distress**
- **Multiple convulsions**
- **Circulatory collapse**, **pulmonary oedema**
- **Abnormal bleeding/DIC**
- Laboratory severity: **severe anaemia**, **hypoglycaemia (<2.2 mmol/L)**, **acidosis**, **renal impairment**, **hyperlactataemia**, **haemoglobinuria**, **hyperparasitaemia** [2].

## 6) Suggested immediate investigations (without delaying treatment)
Guideline investigations that support assessment include [4]:
- **Blood smear**, **packed cell volume/haemoglobin**, **blood sugar**
- **Urinalysis**, **electrolytes/urea & creatinine**
- (Other tests listed include microscopy for stool ova, chest radiograph, CSF studies where indicated) [4].

*Note:* The guideline evidence provided does not detail full supportive-care steps (e.g., oxygen, fluids, glucose correction), so I can’t specify those beyond what’s included in the passages above.

### uncomplicated_malaria_adult

Question: How is uncomplicated malaria treated in an adult?

Checks: `{"answered": true, "citations_valid": true, "expected_sources_present": true, "forbidden_terms_absent": true, "pubmed_retrieved_when_preferred": true, "required_terms_present": true}`

PubMed PMIDs: `39404268, 35916842, 31424703`

Answer:

For an **adult with uncomplicated malaria**, the Nigeria Standard Treatment Guidelines recommend the following approach:

1) **Confirm before treatment**
- **All suspected malaria** cases should have **prompt parasitological confirmation** (microscopy or RDT) before starting treatment [1].
- Diagnosis should not be delayed if there is concern for **severe malaria** [2]—but for *uncomplicated* malaria, the intent is confirmation first [1].

2) **Give an ACT (first-line)**
- **Artemisinin-based Combination Therapy (ACT)** is the recommended treatment for **uncomplicated malaria** [1].
- **Artemether–Lumefantrine (AL)** is the **medicine of choice**; alternatives include **Artesunate–Amodiaquine (AA)**, **Dihydroartemisinin–Piperaquine**, and **Artesunate–Pyronaridine** [1].

### Artemether–Lumefantrine (AL): dosage (adult dosing by weight)
AL dosing is given as **twice daily for 3 days**, with tablet strength depending on weight [1]:

- **≥ 35 kg:** **4 tablets/dose** (20/120 mg tablets) **twice daily x 3 days**, **or** **2 tablets/dose** (40/240 mg tablets) **twice daily x 3 days**, **or** **1 tablet/dose** (80/480 mg tablets) **twice daily x 3 days** [1]

### Alternatives: Artesunate–Amodiaquine (AA)
AA is given as **once daily for 3 days** [1]:
- **36 kg and above (14 years and above):** **2 tablets once daily x 3 days** (100 mg/270 mg per tablet strength) [1]

3) **What to watch for**
- If the illness shows any features suggesting **severe malaria** (e.g., impaired consciousness, prostration, respiratory distress, multiple convulsions, circulatory collapse, etc.), treat as severe malaria rather than uncomplicated [2].
- The available guideline evidence provided here does **not** specify follow-up intervals or specific “monitoring tests” for uncomplicated cases beyond the general recommendation for parasitological confirmation [1], and the general investigations list [4] is not specifically tied to uncomplicated follow-up.

If you tell me the patient’s **weight** (and whether pregnant), I can restate the exact **AL regimen** appropriate for that weight from the guideline tables [1].

### breast_tumour_oncovin

Question: How should breast tumour be managed and what is the dose of Oncovin?

Checks: `{"answered": true, "citations_valid": true, "expected_sources_present": true, "forbidden_terms_absent": true, "pubmed_retrieved_when_preferred": true, "required_terms_present": false}`

PubMed PMIDs: `35367784, 30100074, 38160535`

Answer:

### Management of breast tumour (Nigeria Standard Treatment Guidelines 2022)

**1) Use a multidisciplinary team**
Management is undertaken by a multidisciplinary team (surgeons, medical oncologists, radiation oncologists, pathologists, etc.). [3]

**2) Confirm tissue diagnosis before chemotherapy**
Tissue diagnosis must be established before using chemotherapy. [3]

**3) Main treatment modalities**

**A. Surgery (local control)**
- **Lumpectomy / wide excision / quadrantectomy** **PLUS breast irradiation** [1]
- **Mastectomy**:
  - **Simple mastectomy with axillary clearance**
  - **Modified radical mastectomy** [1]
- Surgery options to aim for adequate margins/lymph node control:
  - **Wide excision**: complete tumour excision with **minimum 2 cm tumour-free margin** in all planes [3]
  - **Radical excision**: tumour excision with **loco-regional control of lymph nodes** [3]
- For localized metastasis, **resection of metastasis (metastatectomy)** may be considered (e.g., localized liver/lung/brain metastases). [3]

**B. Radiotherapy**
- Used especially **after breast-conserving surgery** (breast irradiation is explicitly stated after lumpectomy/wide excision/quadrantectomy). [1]
- (Further details on radiotherapy approach are referenced in the guideline but not included in the supplied text.) [1]

**C. Systemic therapy**
- **Chemotherapy** (for **neoadjuvant** in locally advanced/locoregionally advanced/metastatic disease, and/or **adjuvant** as indicated) [1,3]
- **Combination chemotherapy** may be used depending on immunohistochemistry and performance index, with examples including **EC, AC, FEC, docetaxel, capecitabine, etc.** [1]
- **Hormonal (endocrine) therapy** is dictated by immunohistochemistry: [1]
  - **Tamoxifen**:
    - **20 mg daily for at least 5 years** in **premenopausal** women
    - Postmenopausal: **switch to aromatase inhibitors later** [1]
  - **Aromatase inhibitors** (postmenopausal):
    - **Anastrozole 1 mg daily**
    - **Letrozole 2.5 mg daily**
    - **Exemestane 25 mg daily** [1]
  - **Trastuzumab** for **HER2-positive** tumours [1]

**4) Follow-up & supportive measures**
- Lifestyle modifications (reduce estrogen exposure, quit alcohol/smoking, etc.) [1]
- **Monthly breast self-examination**, **clinical breast examination**, and **periodic imaging** (e.g., mammogram, chest X-ray, abdominal USS, bone scan). [1]
- Supportive care should be arranged, and cancer patients should be referred to specialist care when feasible. [4]

---

### Dose of Oncovin (Vincristine)
The guideline dose of **Oncovin (Vincristine)** is:
- **Vincristine (Oncovin) 1.4 mg/m² IV on Day 8** [2]

*(Note: the supplied evidence is from the “LYMPHOMA – MOPP” regimen section, not breast cancer.)* [2]

### sciatica_management

Question: How should sciatica be managed?

Checks: `{"answered": true, "citations_valid": true, "expected_sources_present": true, "forbidden_terms_absent": true, "pubmed_retrieved_when_preferred": true, "required_terms_present": true}`

PubMed PMIDs: `27175952, 38398287, 34794594`

Answer:

Sciatica is managed as part of **back pain** (pain extending along the spine/buttocks area) with the emphasis on **symptom relief**, **conservative measures first**, and **investigation only if “red flags” are present** [2].

## 1) Assess for “red flags” (need for further investigations)
Most back pain (including mechanical causes such as poor posture/overuse) does **not** need further investigations [2,3].
Be alert for red flags that warrant further investigation/imaging (X-ray/MRI/CT), including:
- back pain disturbing sleep [2]
- pain that persists with recumbent position [2]
- constitutional symptoms (fever, weight loss, nausea, feeling unwell) [2]
- bowel disorders or urinary symptoms [2]
- muscle weakness or deformities [2]
- suspicion of serious causes (e.g., malignancy, osteoporotic fractures, multiple myeloma, TB spine, spinal abscess) [2]

## 2) Non-drug management (initial/first-line)
Use conservative options to relieve pain and improve function [1]:
- **Education** [1]
- **Avoidance of precipitating factors** [1]
- **Weight loss** (if applicable) [1]
- **Physical therapy** [1]
- **Back exercises** (e.g., **Mackenzie Extension Exercises**) [1]
- Other supportive options listed: **acupuncture** and **biofeedback** [1]

## 3) Drug management (for pain control)
Drug treatment is based on analgesia and anti-inflammatory/neuropathic pain agents where appropriate [1]:
- **Simple analgesic:** **Paracetamol up to 1 g three times daily**, with or without other options [1]
- **NSAIDs** (choose one option):
  - **Ibuprofen up to 2,400 mg daily** [1]
  - **Naproxen 500 mg twice daily** [1]
  - **Diclofenac 75 mg twice daily** [1]
  - **COX-2 inhibitor (celecoxib) 200 mg daily** [1]
- **Muscle relaxants** (if needed):
  - **Tizanidine up to 4 mg three times daily** [1]
  - **Baclofen 5–10 mg daily** [1]
- **Tramadol (narcotic analgesic): 50 mg three times daily** [1]
- **For neuropathic-type pain agents:**
  - **Amitriptyline 25–50 mg nocte** [1]
  - **Pregabalin up to 600 mg daily** [1]
  - **Gabapentin up to 1,500 mg daily** [1]

## 4) When to consider investigations (imaging/testing)
Use the guideline approach for back pain: **no imaging if mechanical and no red flags** [2,3].
Investigate with appropriate imaging (plain X-ray/CT/MRI as indicated) and/or labs when red flags are present [2,3].

## 5) Monitoring / safety notes
The provided guideline passage lists general treatment goals and options; it does **not** include sciatica-specific follow-up intervals or NSAID/neuropathic-agent monitoring details. It does note that **steroids** (discussed in a different neurologic section) can cause dyspepsia/hyperglycaemia and should be used with caution after infections are excluded—however this is **not sciatica-specific** in the evidence given [4].

If you share the patient’s red-flag symptoms and duration, I can help map them to the guideline “investigate vs treat conservatively” pathway.

### hypertension_pregnancy

Question: How should hypertension in pregnancy be managed?

Checks: `{"answered": true, "citations_valid": true, "expected_sources_present": true, "forbidden_terms_absent": true, "pubmed_retrieved_when_preferred": true, "required_terms_present": false}`

PubMed PMIDs: `25622379, 20143745, 37308715`

Answer:

At the moment, the clinical evidence you provided does **not** include any Nigeria Standard Treatment Guidelines (2022) passage on **hypertension in pregnancy** (e.g., gestational hypertension, chronic hypertension, or pre-eclampsia), nor specific recommendations on antihypertensive drug choice, BP thresholds, or monitoring for hypertensive disorders in pregnancy.

So, using only the supplied evidence, I **cannot** give an evidence-based management plan for “hypertension in pregnancy.”

What I *can* say from the supplied PubMed context is that hypertensive disorders in pregnancy are serious and management depends on severity and diagnosis, with some sources describing emergency thresholds and the general role of antihypertensives and magnesium sulfate in pre-eclampsia—but these would **not** be Nigeria guideline recommendations because no guideline passage is provided for hypertension in pregnancy [5,6,7].

If you share the Nigeria guideline section/passages specifically titled something like **“Hypertension in Pregnancy / Pre-eclampsia and Eclampsia”**, I can then summarize the recommended Nigeria-based management (BP targets/thresholds, first-line drugs, seizure prophylaxis, investigations, and timing of delivery) using those exact passages.

### type_2_diabetes

Question: How should type 2 diabetes mellitus be managed?

Checks: `{"answered": true, "citations_valid": true, "expected_sources_present": true, "forbidden_terms_absent": true, "pubmed_retrieved_when_preferred": true, "required_terms_present": true}`

PubMed PMIDs: `39940862, 37150579, 35963508`

Answer:

For **type 2 diabetes mellitus (T2DM)**, the Nigeria Standard Treatment Guidelines 2022 emphasize (1) **confirming the diagnosis biochemically before starting treatment**, and (2) building management around **lifestyle/weight-control measures integrated into diabetes care**, with **structured monitoring**. [1,2]

## 1) Confirm diagnosis biochemically (before therapy)
- The diagnosis **must be confirmed biochemically prior to initiation of any therapy**. [1]
- Confirm with one of the following:
  - **Random venous plasma glucose ≥ 11.1 mmol/L (≥200 mg/dL)**, **or**
  - **Fasting venous plasma glucose ≥ 7.0 mmol/L (≥126 mg/dL)**. [1]
- In **asymptomatic** people: a **single abnormal glucose** is **not enough**; you need a **second** fasting/random result above the diagnostic threshold. [1]
- Sometimes a **75 g Oral Glucose Tolerance Test (OGTT)** is used to confirm. [1]

## 2) Core treatment: lifestyle/weight control integrated into diabetes care
T2DM management should include weight and lifestyle interventions:
- Assess **dietary intake, physical activity level, BMI, and waist circumference** at presentation and during monitoring. [3]
- For patients with **BMI > 25**, and **waist circumference >102 cm (men)** or **>88 cm (women)**: **integrate weight-control measures into the overall management of diabetes and comorbidities**. [3]
- **Dietary changes and increased physical activity** are described as the **most economical means to lose weight**. [3]
- Use **education**, **realistic goals**, a **multi-disciplinary approach**, and **record-keeping/goal and weight progress charts**. [3]

> Note: The supplied Nigeria guideline passages do **not** include specific T2DM glucose-lowering drug regimens (e.g., metformin/insulin selection and dosing). So I can’t responsibly give medication start/adjustment instructions from the provided evidence.

## 3) Monitoring (to guide ongoing care)
The guideline monitoring framework includes:
- **Blood glucose** results and **regular self-monitoring** at home (fasting and random testing) using a glucose meter. [1]
- During clinic review: **periodic fasting or random tests**. [1]
- **HbA1c at least three times per year**. [1]
- **Blood lipids annually** (more often if abnormal or on lipid-lowering medication). [1]
- **Blood urea, electrolytes and creatinine annually** (more often if abnormal). [1]
- **Urine protein annually**. [1]

## What the available evidence is missing
From the passages provided, there is **insufficient evidence context** to specify:
- which antihyperglycemic drugs to start for T2DM,
- escalation/intensification steps,
- glycaemic targets,
- when/how to initiate insulin,
because those details are not included in the supplied Nigeria guideline excerpts.

If you share the rest of the Nigeria guideline section on **“Treatment”** for diabetes (or the relevant dosing/algorithm pages), I can summarize the recommended stepwise T2DM regimen and monitoring targets using the same evidence numbering.

### child_pneumonia

Question: How should pneumonia in a child be managed?

Checks: `{"answered": true, "citations_valid": true, "expected_sources_present": true, "forbidden_terms_absent": true, "pubmed_retrieved_when_preferred": true, "required_terms_present": false}`

PubMed PMIDs: `31573350, 41110447, 34481570`

Answer:

### Practical management of pneumonia in a child (Nigeria STG 2022)

#### 1) Immediate supportive care
- **Give oxygen** to maintain **PaO₂ at or above 8 kPa** [1]
- **Give IV fluids**, especially if the case is **severe** [1]
- **Give antipyretics** [1]

#### 2) Start antibiotics (choice depends on age and severity)

##### A. **Age < 2 months**
- **Admit and treat as neonatal sepsis** (no specific CAP antibiotic regimen is listed in the provided excerpt) [1]

##### B. **Age ≥ 2 months**
**Outpatient (first line)**
- **High-dose oral amoxicillin** **90 mg/kg/day** in **2 divided doses** for **at least 5 days** [1]

**Outpatient (alternatives)**
- **Oral amoxicillin–clavulanic acid** (amoxicillin component **90 mg/kg/day**) in **2 divided doses**, OR [1]
- **Oral cefpodoxime** **10 mg/kg/day** in **2 divided doses**, OR [1]
- **Oral cefuroxime** **20–30 mg/kg/day** in **2 divided doses** for **at least 5 days** [1]

**Inpatient (first line)**
- **IV amoxicillin** **150 mg/kg/day** in **3 divided doses** **AND**
- **IV gentamicin** **5 to 7.5 mg/kg/day** [1]

**Inpatient (alternatives)**
- **IV ceftriaxone** **100 mg/kg/day** single dose **or** in **2 divided doses**; OR [1]
- **IV cefotaxime** **50 to 100 mg/kg** in **2 divided doses**; OR [1]
- **IV gentamicin and IV cloxacillin** **100–200 mg/kg/day** in **4 divided doses**; OR [1]
- **IV cefuroxime** **150 mg/kg** in **3 divided doses** **AND IV gentamicin** [1]

##### C. **HIV-infected children**
- **Outpatient (first line):** **High-dose oral amoxicillin 90 mg/kg/day** in **2 divided doses** for **10 days** [1]
- **Outpatient (alternatives):**
  - **amoxicillin–clavulanic acid** (amoxicillin component **90 mg/kg/day**) in **2 divided doses**, OR [1]
  - **cefpodoxime** **10 mg/kg/day** in **2 divided doses**, OR [1]
  - **cefuroxime** **20–30 mg/kg/day** in **2 divided doses** for **at least 10 days** [1]
- **Inpatient (regimen):** **IV amoxicillin 150 mg/kg/day** in **3 divided doses** **AND IV gentamicin 5–7.5 mg/kg/day** **PLUS** **high-dose co-trimoxazole** (**20 mg/kg/day of trimethoprim**) for **at least 10 days** [1]
- **Inpatient alternatives:** **IV ceftriaxone** OR **IV cefotaxime** OR **IV cefuroxime** (as per doses above) **AND IV gentamicin PLUS high-dose co-trimoxazole for at least 10 days** [1]

#### 3) General points on antibiotic duration/route (from STG section)
- **Commence oral therapy as soon as possible** (after initial parenteral treatment when clinically improving) [1]

#### 4) Cautions (adverse effects noted in the STG excerpt)
- **Co-amoxiclav:** nausea, diarrhoea, skin rashes; **contraindicated in penicillin hypersensitivity** [1]
- **Cefuroxime:** nausea/vomiting/abdominal discomfort/headache; rarely antibiotic-associated colitis [1]
- **Macrolides:** similar but usually milder; hepatotoxicity and antibiotic-associated colitis are **rare** [1]

> **Note:** The provided excerpt includes an “Investigations” section title but no usable investigation recommendations in the supplied text [2].

### acute_asthma

Question: How should acute asthma exacerbation be managed?

Checks: `{"answered": true, "citations_valid": true, "expected_sources_present": true, "forbidden_terms_absent": true, "pubmed_retrieved_when_preferred": true, "required_terms_present": true}`

PubMed PMIDs: `35218742, 28689842, 36430683`

Answer:

Acute asthma exacerbation management (Nigeria STG 2022) should aim to **arrest and reverse the acute episode**, with supportive care and bronchodilation, and add escalation medicines if severe. [1]

### 1) Immediate bronchodilation (core treatment)
- **Nebulised salbutamol** [1]
  - **Adult and child >18 months:** **2.5 mg** nebulised, **repeat up to 3 times in the first hour**, then **every 4 hours for the next 24 hours**; **may be increased to 5 mg if necessary**. [1]
  - **Child <18 months:** **1.25–2.5 mg** using the **same schedule**. [1]
  - **Severe cases:** **more frequent administration may be needed**. [1]

### 2) Escalation for life-threatening asthma
If the patient has **life-threatening asthma** and **has not previously been treated with theophylline** (and has no contraindications): [1]
- **IV aminophylline** [1]
  - **Adult:** **125–250 mg slowly over 20 minutes** with **close monitoring**. [1]
  - **Child (1 month–18 years):** **5 mg/kg IV injection (max 500 mg)**, then **IV infusion**. [1]
  **Cautions (from STG):** do **not exceed 500 mg in 24 hours** (cardiac arrhythmia risk); avoid in **elderly**, or in patients with **arrhythmias** and **hyperthyroidism**; use caution in **hypertensive patients**; may cause **CNS stimulation** (insomnia, convulsions). [2]

### 3) Anti-inflammatory treatment (systemic steroids when indicated)
- **Oral or IV steroids where indicated**. [1]
(Exact dose/duration for acute exacerbation isn’t provided in the available acute-exacerbation passage, but oral prednisolone dosing is provided under severe persistent/add-on oral corticosteroid guidance: adult **40–50 mg daily for a few days then reduce gradually**, child **1–2 mg/kg once daily for 3–5 days**.) [2]

### 4) Additional adjuncts in acute severe disease
- **Magnesium sulphate:** **50 mg/kg single dose IV slowly**; **check deep tendon reflexes during administration**. [1]
- **Adequate hydration** and **oxygen**. [1]

### 5) Monitoring/precautions
- **Aminophylline maximum:** **≤500 mg in 24 hours**. [2]
- **Aminophylline:** avoid/precautions as above (arrhythmias, hyperthyroidism, elderly; caution with hypertension; CNS effects). [2]
- **Magnesium sulphate:** **monitor deep tendon reflexes** while giving. [1]
- **STG reminder:** prescribers/dispensers should consult product literature to confirm aerosol strengths. [2]

If you tell me the patient’s **age** and whether this is **life-threatening/severe enough for escalation**, I can map the exact nebulised salbutamol schedule and which add-ons from the STG are supported.

### uti_pregnancy

Question: How should urinary tract infection in pregnancy be managed?

Checks: `{"answered": true, "citations_valid": true, "expected_sources_present": true, "forbidden_terms_absent": true, "pubmed_retrieved_when_preferred": true, "required_terms_present": false}`

PubMed PMIDs: `36031053, 37473414, 37906240`

Answer:

### Practical management of UTI in pregnancy (what the available evidence supports)

**1) Confirm the diagnosis and classify the syndrome**
- Use **urinalysis and urine culture** as helpful diagnostic tools, while recognising that they have limitations; also **differentiate asymptomatic bacteriuria (ASB) from true UTI**, because treatment decisions differ in pregnancy vs non-pregnant patients. [7](https://pubmed.ncbi.nlm.nih.gov/37906240/)

**2) Screen for and manage ASB (asymptomatic bacteriuria)**
- Evidence summaries note that **multiple international guidelines recommend a “single screen-and-treat” approach** to ASB, typically with **screening in the first trimester using only a single urine culture**. [5](https://pubmed.ncbi.nlm.nih.gov/36031053/)
- Treatment of ASB (when chosen) is associated with **reduced low birth weight and preterm birth**, which is one reason screening is justified. [5](https://pubmed.ncbi.nlm.nih.gov/36031053/)

**3) If treating ASB, favour a short course of commonly used options**
- If the clinician opts to treat ASB, the review evidence suggests **favouring a short course of a β-lactam, nitrofurantoin, or fosfomycin**. [5](https://pubmed.ncbi.nlm.nih.gov/36031053/)

**4) Treat symptomatic cystitis**
- The available evidence context states that **data on cystitis in pregnancy are limited**, so the evidence provided here is not specific about exact regimens for cystitis beyond general antimicrobial choices used for UTI in pregnancy. [5](https://pubmed.ncbi.nlm.nih.gov/36031053/)

**5) If pyelonephritis is suspected/confirmed, treat as a higher-risk infection**
- Acute pyelonephritis is linked with **increased maternal complications**, and in some studies **preterm delivery and low birth weight**. [5](https://pubmed.ncbi.nlm.nih.gov/36031053/)
- Preferred antimicrobials mentioned for pyelonephritis include:
  - **Amoxicillin combined with an aminoglycoside**
  - **Third-generation cephalosporins**
  - **Carbapenems** [5](https://pubmed.ncbi.nlm.nih.gov/36031053/)

**6) Ongoing care**
- Because UTIs span a spectrum (ASB → cystitis → pyelonephritis), care should focus on **recognition, diagnosis, and appropriate treatment** to reduce adverse outcomes. [6](https://pubmed.ncbi.nlm.nih.gov/37473414/)

---

### What is *not* answerable from the evidence you provided
- There are **no Nigeria Standard Treatment Guidelines passages included for UTIs in pregnancy**, and no **specific Nigerian dosing regimens** for UTI syndromes in pregnancy are provided in your supplied materials. So I can’t safely give drug *doses/durations* for pregnancy UTI from the current evidence set.

If you share your guideline passages for **UTI in pregnancy** (or the local regimen table), I can convert the above into the exact Nigerian recommended drugs, doses, and durations.

### irrelevant_crypto

Question: What is the best cryptocurrency to buy today?

Checks: `{"answered": true, "citations_valid": true, "expected_sources_present": true, "forbidden_terms_absent": true, "pubmed_retrieved_when_preferred": true, "required_terms_present": false}`

PubMed PMIDs: `35980104, 33801075, 38540527`

Answer:

I can’t answer that safely or appropriately from the evidence provided. The clinical guideline and PubMed passages you shared are about **neonatal sepsis, HIV prophylaxis, malaria treatment, and prostate carcinoma**—none of them provide information relevant to choosing a **cryptocurrency to buy**.

If you want, share evidence or criteria specific to crypto (e.g., risk tolerance, investment horizon, and the specific coins you’re considering), and I can help you reason through it—but with the current material, the available evidence context is insufficient for the question.
