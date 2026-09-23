---
title: Centinela Sísmico
emoji: 🛡️
colorFrom: blue
colorTo: gray
sdk: static
pinned: false
license: mit
---

# 🛡️ Centinela Sísmico *(Global Seismic Sentinel)*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![PWA Zero-Network](https://img.shields.io/badge/PWA-Instalable%20en%20Celular-teal)](https://neurodeveloper11.github.io/centinela-sismico/)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-%40neurodeveloper-FFD21E?logo=huggingface&logoColor=black)](https://huggingface.co/neurodeveloper)
[![USGS Live API](https://img.shields.io/badge/USGS-Real--Time%20GeoJSON-green)](https://earthquake.usgs.gov)
[![Standards: WHO PAP & ATC-20](https://img.shields.io/badge/Standards-WHO%20PAP%20%7C%20ATC--20-purple)](https://www.who.int)

> **El vigía que calcula la onda destructiva antes de que llegue a tu hogar.**  
> *Alerta temprana anticipada por GPS, detector de mesa con 0ms de latencia, serenidad guiada y botiquín familiar.*  
> *Concebido e implementado por **Fabio Ignacio Torres Benítez** (Psicólogo, Científico Cognitivo e Ingeniero de Datos / IA).*  
> **100% Gratuito, Libre y Accesible para Cualquier Persona en el Mundo.**

---

## 🌍 The Global Problem: Why Earthquake Apps Fail Humans

Earthquakes affect over **2.8 billion people** across the globe, from the Pacific Ring of Fire (Japan, Indonesia, Chile, Colombia, Mexico, California) to the Alpine-Himalayan belt (Turkey, Greece, Italy, Iran).

While existing technological solutions (USGS, EMSC, JMA, Google Android Alerts) focus exclusively on **pure geophysics** (magnitude, depth, epicenter) or provide a 5-second preliminary alarm:

1. **The Human Panic Crisis:** The overwhelming majority of serious injuries and secondary fatalities during and immediately after shaking occur due to acute panic: stampedes down stairwells, jumping from windows, cardiac events, hyperventilation, and motor freezing.
2. **Infrastructure & Telecom Collapse:** In high-magnitude events, 4G/5G mobile networks saturate or fail completely within 120 seconds due to calling spikes and video traffic. Heavy applications fail to load.
3. **Misinformation Pandemics:** Viral hoaxes (*"A mega 9.0 earthquake has been predicted for 6:00 PM tonight"*) spread across messaging apps, terrorizing traumatized populations.
4. **Post-Shaking Cognitive Overload:** Regular citizens cannot decipher whether a crack in their wall is dangerous or cosmetic, nor do they know how to deliver **Psychological First Aid (PAP)** to a hysterical child or hyperventilating family member.

**QuakeMind Global bridges this divide.** It unites **Geophysical Data Science** with **Emergency Psychology & Cognitive Science**, offering a dual-layer ecosystem: an intelligent cloud Space and an ultra-resilient zero-network offline PWA.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph INGESTION ["1. Global Data Ingestion (0ms Cost)"]
        USGS["USGS Global Feeds (GeoJSON API)"]
        EMSC["EMSC Euro-Med / Global API"]
        GPS["Browser Geodesic Coordinates / City Preset"]
    end

    subgraph ENGINE ["2. Shared Science Core (pwa/seismic-core.js ≡ quakemind_engine.py)"]
        HAVERSINE["3D Hypocentral Distance: R = sqrt(D² + h²)"]
        GMPE["Intensity Prediction Equation (Allen, Wald & Worden 2012) ± σ"]
        MMI["Local Modified Mercalli Intensity (MMI I–XII)"]
        DECIDE["Alert decision: incoming / felt / calm + cross-source de-duplication"]
        PAP["WHO / ABCDE Psychological First Aid Engine"]
        ATC20["ATC-20 Post-Earthquake Building Safety Triage"]
        FACT["NLP Semantic Rumor & Myth Debunker"]
    end

    subgraph DEPLOYMENT ["3. Public Delivery Ecosystem"]
        HF_SPACE["Hugging Face Space (Gradio 5 Multi-Tab UI)"]
        PWA_OFFLINE["GitHub Pages PWA (Zero-Network Service Worker)"]
        DATASET["Hugging Face Open Dataset (Apache Parquet)"]
    end

    INGESTION --> ENGINE
    ENGINE --> DEPLOYMENT
```

---

## ✨ Core Capabilities & Scientific Foundation

### 1. 📡 Live Global Seismic Monitor & Local Shaking Calculator
* **Multi-Source Ingestion:** Ingests live USGS feeds (`all_hour`, `day_all`, `4.5_day`, `significant_month`) with local cache fallback in case of connection dropouts.
* **Intensity Prediction Equation (IPE):** Translates raw geophysical data ($M$, depth $h$, epicentral distance $D$) into the **hypocentral 3D slant distance** $R = \sqrt{D^2 + h^2}$ and estimates the **Modified Mercalli Intensity (MMI I–XII)** with the peer-reviewed global model of **Allen, Wald & Worden (2012)** for active crustal regions (coefficients verified against OpenQuake's `AllenEtAl2012Rhypo`):
  $$\text{MMI} = 2.085 + 1.428\,M - 1.402\,\ln\sqrt{R^2 + R_M^2} + 0.078\,\ln(R/50)\,\big|_{R>50}, \qquad R_M = -0.209 + 2.042\,e^{M-5}$$
  The app always shows the model uncertainty $\sigma = 0.82 + 0.37/(1+(R/22.9)^2)$ (≈ 0.8–1.2 MMI units) as a likely range.
* **One science core, two languages:** `pwa/seismic-core.js` (browser, Service Worker, Node tests) and `quakemind_engine.py` implement the same equations; a parity test checks 200 random cases to 1e-9.
* **Honest early warning:** the S-wave countdown is computed from the absolute arrival time (no drift when the phone throttles timers). Agencies publish events with a delay (seconds via the EMSC live WebSocket, minutes via bulletins), so near the epicenter the wave often arrives first. In that case the app does **not** stay silent: it shows a *"strong quake likely felt in your area"* notice with post-event guidance.
* **One alert per earthquake:** the same quake reported by EMSC (WebSocket), USGS (feed) and the USGS radial query under different IDs triggers a single alert.
* **Human-Centric Translation:** Instead of confusing numbers, it tells the citizen: *"At your location, shaking was felt as MMI IV (Light). Structural damage to modern buildings is statistically improbable. Breathe calmly."*

### 2. 🛡️ Intelligent Geodesic Filtering & Zero Alarm Fatigue (Cero Fatiga de Alarma)
* **Perceived Impact Thresholding:** Eradicates acute adrenaline spikes and alarm fatigue caused by distant or minor earthquakes (e.g. M 4.2 at 350 km, MMI I–II) that the user will never feel. The acoustic siren and urgent countdown **strictly activate if and only if $\text{MMI}_{\text{local}} \ge \text{threshold}$** (default MMI IV: Moderate).
* **Customizable Citizen Profiles:** Users can select between:
  * `🛡️ MMI IV+ (Perceptible / Recommended)`
  * `⚡ MMI V+ (Severe Alerts Only — High intensity)`
  * `🔍 MMI III+ (Light Shaking)`
  * `🔕 Silent Mode (Discreet Vibration Only / 0 dB — Designed for sensory sensitivities, autism, and sleeping infants)`
* **Active Calm Reassurance:** If a regional earthquake occurs within 500 km but is imperceptible at the user's coordinates, the Reassurance Shield explicitly confirms: *"Detected M4.5 at 240 km. At your location perceived intensity is MMI 1.7 (Imperceptible). Your home and family are safe."* This prevents panic generated by social media rumors.

### 3. 🌍 World Pulse: 24-Hour Serene Earth Catalog
* **Global Activity Window:** Clean, non-alarmist interactive feed showcasing earthquakes from the last 24 hours (USGS `all_day.geojson`).
* **Regional Filters:** Fast category tabs for **Mundo (Global)**, **Latinoamérica** (Colombia, Venezuela, Chile, Mexico, etc.), **Asia / Pacífico**, **Europa / Mediterráneo**, and **Norteamérica**.
* **Personalized Local Safety Context:** Every card calculates real-time distance to user GPS coordinates and estimated local intensity (*"Distance: 1,840 km • Local impact: Imperceptible (MMI I) — Safe"*).

### 4. 🔋 Battery-Optimized Adaptive Micro-Polling
* **Page Visibility API:** Polling runs at 15s in foreground and automatically relaxes to 75s when the browser tab is hidden or phone screen is turned off, reducing background radio and CPU consumption by ~80%.
* **Battery Status API Integration:** Automatically throttles active polling if battery level drops below 20% without charging.
* **Network Backoff:** Implements exponential backoff (30s $\to$ 60s $\to$ 120s) on connection drops to avoid battery-draining error loops.

### 5. 🧠 Human-Centric Psychological First Aid (PAP)
* **Standardized Protocol:** Engineered under **WHO / PAHO guidelines** and the **ABCDE Crisis Intervention Model**:
  * **A (Active Grounding 5-4-3-2-1):** Deactivates dissociation, depersonalization, and panic tunnel vision.
  * **B (Breathing Retraining):** 4-4-7 Cyclic Sighing pacer designed to trigger parasympathetic vagal braking, stopping hyperventilation and tremors.
  * **C (Categorization of Needs):** Isolates actionable priorities: bleeding, gas leaks, structural stability.
  * **D (Support Networks):** Guidelines for responsible communication (single brief SMS instead of network-jamming calls/videos).
  * **E (Psychoeducation):** Normalizes acute stress responses (involuntary muscle shivering, vestibular "phantom quakes") as healthy biological adrenaline discharges.

### 6. 🏗️ ATC-20 Citizen Structural Safety Triage
* Aligned with the **Applied Technology Council (ATC-20)** and seismic building codes (**NSR-10** Colombia, **COVENIN** Venezuela, **FEMA** USA):
  * 🟢 **GREEN TAG (Inspected - Safe to Occupy):** Hairline/cosmetic cracks in plaster (< 1-2 mm).
  * 🟡 **YELLOW TAG (Restricted Use - Caution):** Horizontal masonry cracks (2-5 mm) or non-bearing wall distress.
  * 🔴 **RED TAG (Unsafe - Evacuate Immediately):** Diagonal 45° 'X' shear cracks crossing structural columns/beams, exposed buckled rebar, wall tilting, or gas leaks.

### 7. 🔊 Zero-Network Offline Survival PWA (GitHub Pages)
Operates with **0 bytes of internet connection** once saved to the device:
* **3,500 Hz Acoustic Rescue Beacon:** Uses the native browser **Web Audio API** to synthesize a pure, high-penetration 3,500 Hz tone pulsing standard Morse code SOS (`... --- ...`). This specific frequency matches the resonance of the human ear canal, allowing trapped or blackout victims to guide search and rescue teams **without shouting or vocal exhaustion**.
* **Visual Screen Strobe:** High-contrast alternating flashing beacon for night rescue.
* **Offline 72-Hour Survival Backpack:** Interactive checklist saved permanently in `localStorage`.
* **Emergency Family ID Card Generator:** Renders a high-resolution identification badge on an HTML5 `<canvas>` and exports to PNG directly on the phone without servers.

### 8. 🔍 NLP Seismic Myth-Buster & Rumor Debunker
* Rigorously debunks viral hoaxes using geophysics and statistics:
  * Deterministic time/hour predictions $\to$ Why tectonic friction nucleation is a chaotic non-linear process.
  * "Earthquake weather / Hot muggy air" $\to$ Atmospheric troposphere vs. lithospheric depth physics.
  * Animals sensing quakes $\to$ Sensory perception of high-frequency P-waves (seconds before) vs. fake hour-long forecasts.
  * "Triangle of life" $\to$ Why official agencies mandate **Drop, Cover, and Hold On**.

---

## 🚀 Quickstart & Local Installation

### Prerequisites
* Python 3.11 or higher
* Modern web browser (Chrome, Firefox, Safari, Edge)

### 1. Clone the Repository
```bash
git clone https://github.com/neurodeveloper11/centinela-sismico.git
cd centinela-sismico
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Automated Quality Gate
```bash
npm install                        # test tooling only (playwright-core uses your installed Chrome)
python scripts/verify_all.py       # every success criterion → 🟢 ÉXITO / 🔴 FALLO
```
The gate runs, without touching the network:
* **Python** (`pytest tests/test_quakemind.py`): geophysics, IPE reference values, EMSC/USGS parsing with fixtures, alert decisions, PAP, ATC-20, myth-buster and a **Python ↔ JavaScript parity** test.
* **JavaScript** (`npm test`): the shared `seismic-core.js`, including a speed budget (10 000 evaluations < 200 ms).
* **End-to-end** (`npm run test:e2e`): the real PWA in headless Chrome with a simulated EMSC WebSocket and USGS feeds — alert latency, countdown accuracy, no duplicate alerts, no false alarm for deep quakes, "felt" notice, XSS, photosensitive-safe strobe, language persistence and full offline load.

Optional live checks against the real agencies: `RUN_NETWORK_TESTS=1 pytest -k Live` and `node tests/e2e/live-smoke.mjs`.

After editing anything in `pwa/`, run `python scripts/sync_dist.py` to copy it to `docs/` (GitHub Pages) and the repository root (Hugging Face Space). It refuses to publish Git LFS pointer files instead of images.

### Continuous Integration & GitHub Pages
`.github/workflows/ci-pages.yml` runs the whole gate on every push and pull request and deploys `docs/` to GitHub Pages from `main`, checking out Git LFS so icons and the preview image are real PNGs. **One-time setup:** *Settings → Pages → Build and deployment → Source: GitHub Actions*.

### 4. Launch the Hugging Face Space App Locally
```bash
python app.py
```
Open your browser at `http://localhost:7860`.

### 5. Launch the Offline PWA Locally
Simply open `pwa/index.html` in any web browser or serve via Python:
```bash
cd pwa
python -m http.server 8080
```
Visit `http://localhost:8080` on your mobile phone or desktop, and select **"Add to Home Screen"** to enable 100% offline functionality.

---

## 📦 Hugging Face Open Dataset

The project includes an automated global seismic dataset builder:
```bash
python scripts/build_hf_dataset.py
```
Generates:
* `dataset/global_seismic_risk_catalog.parquet` (Ultra-compressed Apache Parquet)
* `dataset/global_seismic_risk_catalog.csv`

Variables included: `event_id`, `title`, `place`, `magnitude`, `magnitude_type`, `depth_km`, `depth_category`, `latitude`, `longitude`, `time_iso_utc`, `seismic_energy_joules`, `usgs_alert_level`, `felt_reports_count`, `usgs_mmi`, `tsunami_alert`.

---

## 🔬 Scientific & Bibliographical References

1. **Allen, T. I., Wald, D. J., & Worden, C. B. (2012).** *Intensity attenuation for active crustal regions.* Journal of Seismology, 16(3), 409-433. (Intensity prediction equation used by the app.)
1. **Wald, D. J., Quitoriano, V., Heaton, T. H., & Kanamori, H. (1999).** *Relationships between Peak Ground Acceleration, Peak Ground Velocity, and Modified Mercalli Intensity in California.* Earthquake Spectra, 15(3), 557-564.
2. **Worden, C. B., Gerstenberger, M. C., Rhoades, D. A., & Wald, D. J. (2012).** *Probabilistic relationships between ground-motion parameters and Modified Mercalli Intensity in New Zealand.* Bulletin of the Seismological Society of America, 102(3), 893-921.
3. **World Health Organization (WHO), War Trauma Foundation & World Vision International (2011).** *Psychological first aid: Guide for field workers.* WHO, Geneva.
4. **Applied Technology Council (ATC-20).** *Procedures for Postearthquake Safety Evaluation of Buildings.* Redwood City, CA.
5. **Asociación Colombiana de Ingeniería Sísmica (AIS).** *Reglamento Colombiano de Construcción Sismo Resistente (NSR-10).*
6. **Huberman, A. D. et al. (2023).** *Brief structured respiration practices enhance mood and reduce physiological arousal.* Cell Reports Medicine, 4(1), 100895.

---

## 👤 Author & Lead Architect

**Fabio Ignacio Torres Benítez**  
*Data Engineer | Cognitive Scientist & Clinical/Organizational Psychologist | Full-Stack AI Developer*  
📍 Cali / Buenaventura, Colombia  
🔗 [LinkedIn](https://www.linkedin.com/in/fabio-torres-39364b258) | [GitHub](https://github.com/neurodeveloper11) | [Hugging Face](https://huggingface.co/neurodeveloper) | [Google Play (NeuroGym Live)](https://play.google.com/store/apps/details?id=com.t11.neurochess&hl=es_419)

---

## 📄 License
This project is licensed under the **MIT License** — free to use, modify, study, and distribute for humanitarian, educational, and commercial purposes worldwide.
