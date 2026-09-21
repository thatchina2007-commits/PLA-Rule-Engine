#  PLA-Based Rule Engine Designer

**Modern, Responsive, and Professional Programmable Logic Array (PLA) CAD & Simulation Platform**
Designed in alignment with the **EC2201 / CS8351 Digital Principles & System Design** curriculum (Unit IV: Programmable Logic Devices).

---

## 🌟 Overview

The **PLA-Based Rule Engine Designer** is an interactive engineering CAD workbench that models, synthesizes, minimizes, and simulates Programmable Logic Arrays (PLAs). It bridges the gap between theoretical Boolean algebra and physical digital electronics hardware.

### Key Capabilities
- **Boolean Rule Designer**: Define rules using variables $A, B, C, D$ and algebraic operators (`AND`, `OR`, `NOT`, `XOR`).
- **Product Term Generator**: Automatically synthesizes unique product terms ($P_0, P_1, \dots$) and configures the fusible crosspoint links across the 8 input rails ($A, \overline{A}, B, \overline{B}, C, \overline{C}, D, \overline{D}$).
- **Quine-McCluskey Minimization**: Computes Prime Implicants, Essential Prime Implicants, and minimal Sum-of-Products (SOP) representations.
- **Output Mapping & OR Plane**: Route product terms into multiple outputs ($Y_1, Y_2, Y_3, Y_4$).
- **Complete Truth Table**: Full 16-row ($m_0 \dots m_{15}$) functional truth table with 1-click CSV/JSON export.
- **Interactive PLA Simulator**: Real-time hardware toggle switches for $A, B, C, D$, animated signal flows along active rails, and dynamic LED logic indicators.
- **Conflict & Hazard Detection**: Automated scanning for duplicate product terms, contradictory output assignments, and subsumption (absorption) redundancies.
- **Automated Test Suite**: 10 Normal operational cases + 5 Edge/Fault test cases with live pass/fail diagnostics.
- **Data Analytics Dashboard**: Chart.js charts showing output duty cycles, PLA matrix crosspoint density, and input switching sensitivities.
- **Academic References**: Cited textbook chapters from Morris Mano, Floyd, and EC2201 syllabus mapping.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ (Installed at `C:\Users\ASUS TUF\AppData\Local\Programs\Python\Python312`)

### 1. Install Dependencies
```bash
cd backend
python -m pip install -r requirements.txt
```

### 2. Launch the Application
Run the launcher script from the root directory:
```cmd
run.bat
```
Or start the Flask server directly:
```bash
python backend/app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

*Note: The frontend is fully equipped with an offline client-side simulation engine, so you can also open `frontend/index.html` directly in any web browser without a server!*

---

## 📂 Project Architecture

```
pla-rule-engine/
├── backend/
│   ├── app.py                     # Flask REST API server & static web server
│   ├── pla_engine.py              # Boolean parsing, matrix compiler, Quine-McCluskey, conflict detector
│   ├── database.py                # SQLite persistence (rules, outputs, test cases, audit log)
│   ├── synthetic_data.py          # Benchmark dataset generators and fault injectors
│   └── requirements.txt           # Flask, Flask-Cors, NumPy, Pandas
├── frontend/
│   ├── index.html                 # Complete 13-module responsive single-page application
│   ├── css/
│   │   └── styles.css             # Cyberpunk circuit theme, glowing neon accents, print stylesheet
│   └── js/
│       ├── api.js                 # REST client with transparent client-side fallback
│       ├── pla_core.js            # Client-side Boolean logic and truth table engine
│       ├── visualizer.js          # Interactive Canvas visualizer for PLA AND/OR matrices
│       └── app.js                 # UI coordinator, live switches, test runner, Chart.js
├── data/
│   └── pla_engine.db              # SQLite relational database
├── tests/
│   └── test_engine.py             # Automated unit tests
├── README.md                      # Documentation and academic syllabus mapping
└── run.bat                        # One-click Windows startup batch script
```

---

## 📚 Academic & Curriculum References
- **M. Morris Mano & Michael D. Ciletti**, *Digital Design: With an Introduction to the Verilog HDL*, 5th Edition, Pearson Education. (Chapter 7: Memory and Programmable Logic).
- **Thomas L. Floyd**, *Digital Fundamentals*, 11th Edition, Pearson Education.
- **Anna University EC2201 / CS8351**, *Digital Principles and System Design*, Unit IV: Programmable Logic Devices (PLDs).
