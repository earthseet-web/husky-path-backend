"""Builds backend/data/*.json for husky-path-backend from catalog facts collected on 2026-11-16.

Prerequisite format (used by checks.py):
  "prereq": [group, group, ...]   -> ALL groups must be met
  group = {"any_of": [option, ...], "concurrent_ok": bool, "min_grade": float|None, "alt": str|None}
  option = "CODE" or ["CODE", "CODE"] (a list means all of those courses together)
"""
import json, pathlib, sys

OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "backend/data")
OUT.mkdir(parents=True, exist_ok=True)
CHECKED = "2026-11-16"


def g(*opts, conc=False, grade=None, alt=None):
    return {"any_of": list(opts), "concurrent_ok": conc, "min_grade": grade, "alt": alt}


def dept_url(code):
    dept = code.rsplit(" ", 1)[0].replace(" ", "").lower()
    page = {"ee": "ee", "math": "math", "amath": "amath", "phys": "phys", "chem": "chem", "cse": "cse",
            "stat": "stat", "inde": "inde", "biol": "biol", "engr": "engr"}[dept]
    num = code.rsplit(" ", 1)[1]
    return f"https://www.washington.edu/students/crscat/{page}.html#{dept}{num}"


C = []


def course(code, title, credits, desc, prereq_text, prereq=None, offered=None, areas=None,
           recommended=None, credits_max=None, notes=None):
    C.append({
        "code": code, "title": title, "credits": credits, "credits_max": credits_max or credits,
        "description": desc, "prereq_text": prereq_text or "None listed",
        "prereq": prereq or [], "recommended": recommended, "offered": offered,
        "areas": areas or [], "url": dept_url(code), "notes": notes, "source_checked": CHECKED,
    })


# ---------------- Mathematics ----------------
course("MATH 124", "Calculus with Analytic Geometry I", 5,
       "Single-variable calculus focused on differentiation and its applications.",
       "None listed. Recommended: completion of Department of Mathematics' Guided Self-Placement.",
       offered="AWSpS", areas=["NSc", "RSN"])
course("MATH 125", "Calculus with Analytic Geometry II", 5,
       "Continues single-variable calculus with an emphasis on integration and applications.",
       "Either minimum grade of 2.0 in MATH 124, score of 3 on AB advanced placement test, or score of 3 on BC advanced placement test.",
       [g("MATH 124", grade=2.0, alt="AP Calculus AB or BC score of 3")], offered="AWSpS", areas=["NSc"])
course("MATH 126", "Calculus with Analytic Geometry III", 5,
       "Vector geometry, vector functions, multivariable differential calculus, and Taylor series.",
       "Either a minimum grade of 2.0 in MATH 125, a minimum grade of 2.0 in MATH 135, or a minimum score of 4 on BC advanced placement test.",
       [g("MATH 125", "MATH 135", grade=2.0, alt="AP Calculus BC score of 4")], offered="AWSpS", areas=["NSc"])
course("MATH 134", "Accelerated (Honors) Calculus", 5,
       "First course of the two-year honors sequence covering MATH 124-126 and 207-208.",
       "None listed.", offered="A", areas=["NSc", "RSN"])
course("MATH 135", "Accelerated (Honors) Calculus", 5,
       "Second course of the first-year honors calculus sequence.",
       "A minimum grade of 2.0 in MATH 134.", [g("MATH 134", grade=2.0)], offered="W", areas=["NSc"])
course("MATH 136", "Accelerated (Honors) Calculus", 5,
       "Completes the first-year honors calculus sequence; overlaps with MATH 126.",
       "A minimum grade of 2.0 in MATH 135.", [g("MATH 135", grade=2.0)], offered="Sp", areas=["NSc"])
course("MATH 207", "Introduction to Differential Equations", 4,
       "Ordinary differential equations: first- and second-order equations and the Laplace transform.",
       "A minimum grade of 2.0 in MATH 125.", [g("MATH 125", grade=2.0)], offered="AWSpS", areas=["NSc"])
course("MATH 208", "Matrix Algebra with Applications", 4,
       "Linear systems, vector spaces, matrices, orthogonality, eigenvalues, and applications.",
       "None listed. Recommended: completion of Department of Mathematics' Guided Self-Placement.",
       offered="AWSpS", areas=["NSc", "RSN"])
course("MATH 224", "Advanced Multivariable Calculus", 4,
       "Multivariable integration, vector fields, and the theorems of Green, Stokes, and Gauss.",
       "A minimum grade of 2.0 in either MATH 126 or MATH 136.", [g("MATH 126", "MATH 136", grade=2.0)],
       offered="AWSpS", areas=["NSc"])
course("AMATH 351", "Introduction to Differential Equations and Applications", 3,
       "Ordinary differential equations with Taylor series and Laplace transforms, using science and engineering examples.",
       "MATH 125 or MATH 135.", [g("MATH 125", "MATH 135")], offered="AWSpS", areas=["NSc"])
course("AMATH 352", "Applied Linear Algebra and Numerical Analysis", 3,
       "Numerical methods and linear algebra, including eigenvalue problems, using MATLAB and/or Python.",
       "MATH 126 or MATH 136.", [g("MATH 126", "MATH 136")], offered="AWSpS", areas=["NSc"])
course("STAT 390", "Statistical Methods in Engineering and Science", 4,
       "Probability and statistics for engineering and science, with hands-on computing.",
       "Either MATH 126 or MATH 136.", [g("MATH 126", "MATH 136")], offered="AWSpS", areas=["NSc"])
course("IND E 315", "Probability and Statistics for Engineers", 3,
       "Probability theory and statistics applied to engineering problems and data analysis.",
       "Either MATH 135, MATH 136, MATH 207, or AMATH 351.", [g("MATH 135", "MATH 136", "MATH 207", "AMATH 351")],
       offered="AWS", areas=["NSc"])

# ---------------- Sciences ----------------
course("PHYS 121", "Mechanics", 5,
       "Basic principles of mechanics with lab, for physical science and engineering majors.",
       "Either MATH 124 or MATH 134, which may be taken concurrently.",
       [g("MATH 124", "MATH 134", conc=True)], offered="AWSpS", areas=["NSc", "RSN"])
course("PHYS 122", "Electromagnetism", 5,
       "Fundamentals of electromagnetism with lab, for physical science and engineering majors.",
       "Either PHYS 121 or PHYS 141; and either MATH 125 or MATH 134, which may be taken concurrently.",
       [g("PHYS 121", "PHYS 141"), g("MATH 125", "MATH 134", conc=True)], offered="AWSpS", areas=["NSc"])
course("PHYS 123", "Waves, Light, and Heat", 5,
       "Oscillations, light and optics, fluids, and heat, with lab and tutorial.",
       "Either PHYS 122 or PHYS 142; and either MATH 126 or MATH 134, which may be taken concurrently.",
       [g("PHYS 122", "PHYS 142"), g("MATH 126", "MATH 134", conc=True)], offered="AWSpS", areas=["NSc"])
course("PHYS 141", "Honors Mechanics", 5,
       "Honors version of PHYS 121 in greater depth, for students with strong calculus preparation.",
       "Either a minimum grade of 2.5 in MATH 124, MATH 134 (may be concurrent), a minimum score of 4 on AP Calculus AB, or 3 on AP Calculus BC.",
       [g("MATH 124", "MATH 134", conc=True, grade=2.5, alt="AP Calculus AB score of 4 or BC score of 3")],
       offered="A", areas=["NSc"])
course("PHYS 142", "Honors Electromagnetism", 5,
       "Honors version of PHYS 122 in greater depth.",
       "A minimum grade of 2.5 in PHYS 141; and MATH 125 or MATH 134, either of which may be taken concurrently.",
       [g("PHYS 141", grade=2.5), g("MATH 125", "MATH 134", conc=True)], offered="W", areas=["NSc"])
course("CHEM 142", "General Chemistry I", 5,
       "Atomic nature of matter, bonding, molecular geometry, and stoichiometry, with lab.",
       "Either a minimum grade of 1.7 in CHEM 110, a passing score in the General Chemistry Placement exam, or a minimum score of 1 on the Chemistry AP exam; recommended: MATH 120 or MATH 124.",
       [g("CHEM 110", grade=1.7, alt="General Chemistry Placement exam or AP Chemistry score")],
       offered="AWSpS", areas=["NSc", "RSN"])
course("CHEM 143", "Accelerated General Chemistry I", 6,
       "Accelerated general chemistry covering about half of the year-long sequence, with lab.",
       "Same as CHEM 142.", [g("CHEM 110", grade=1.7, alt="General Chemistry Placement exam or AP Chemistry score")],
       offered="A", areas=["NSc", "RSN"])
course("CHEM 145", "Honors General Chemistry", 5,
       "Honors chemistry covering CHEM 142, 152, and 162 topics with more mathematical rigor.",
       "MATH 124 or MATH 134 (may be concurrent) and an honors placement score, AP Chemistry 3, or IB HL chemistry 5.",
       [g("MATH 124", "MATH 134", conc=True)], offered="A", areas=["NSc", "RSN"],
       notes="Also requires a placement or exam score, which this app cannot check.")
course("BIOL 130", "Introduction to Neuroscience", 4,
       "How brain circuits process sensory information and generate movement.",
       "None listed.", offered="Sp", areas=["NSc"])
course("BIOL 220", "Introductory Biology", 5,
       "Final course of the introductory biology series: animal and plant physiology.",
       "Minimum grade of 2.0 in either BIOL 200, B BIO 200, or T BIOL 140.",
       [g("BIOL 200", "B BIO 200", "T BIOL 140", grade=2.0)], offered="AWSpS", areas=["NSc"])

# ---------------- Programming / Engineering ----------------
course("CSE 121", "Introduction to Computer Programming I", 4,
       "Programming for beginners: methods, loops, conditionals, and arrays.",
       "None listed. Recommended: completion of Paul G. Allen School's Guided Self-Placement.",
       offered="AWSpS", areas=["NSc", "RSN"])
course("CSE 122", "Introduction to Computer Programming II", 4,
       "Program design, style, decomposition, and data structures such as lists, dictionaries, and sets.",
       "None listed. Recommended: CSE 121 or completion of Paul G. Allen School's Guided Self-Placement.",
       offered="AWSpS", areas=["NSc", "RSN"], recommended="CSE 121")
course("CSE 123", "Introduction to Computer Programming III", 4,
       "Data structures and algorithms with linked references, recursion, and inheritance.",
       "None listed. Recommended: CSE 122 or completion of Paul G. Allen School's Guided Self-Placement.",
       offered="AWSpS", areas=["NSc", "RSN"], recommended="CSE 122")
course("CSE 142", "Computer Programming I", 4,
       "Core programming for beginners: methods, control structures, file processing, arrays, objects.",
       "None listed.", offered="AWSpS", areas=["NSc", "RSN"])
course("CSE 143", "Computer Programming II", 5,
       "Data abstraction, linked lists, stacks, queues, binary trees, and recursion.",
       "CSE 142.", [g("CSE 142")], offered="AWSpS", areas=["NSc", "RSN"])
course("CSE 160", "Data Programming", 4,
       "Python for data tasks: analysis, file processing, and visualization.",
       "None listed.", areas=["NSc", "RSN"])
course("CSE 163", "Intermediate Data Programming", 4,
       "Working with varied data types and libraries to write medium-scale programs.",
       "Either CSE 122, CSE 123, CSE 142, CSE 143, or CSE 160.",
       [g("CSE 122", "CSE 123", "CSE 142", "CSE 143", "CSE 160")], areas=["RSN"])
course("CSE 373", "Data Structures and Algorithms", 4,
       "Trees, graphs, hashing, sorting, and other core data structures and algorithms, for non-majors.",
       "CSE 123 or CSE 143.", [g("CSE 123", "CSE 143")])
course("CSE 374", "Intermediate Programming Concepts and Tools", 3,
       "C/C++ programming, manual memory management, and software development tools.",
       "CSE 123 or CSE 143.", [g("CSE 123", "CSE 143")])
course("ENGR 101", "Engineering Exploration", 1,
       "Talks and discussions introducing engineering disciplines and current research.",
       "None listed.")
course("ENGR 321", "Engineering Internship Education", 1,
       "Approved engineering internship that applies classroom theory on the job.",
       "None listed.", offered="AWSpS", credits_max=13,
       notes="Max 4 credits count toward Advanced ECE Electives; max 6 combined with E E 499.")

# ---------------- Electrical & Computer Engineering ----------------
EE_CORE_215_MATH = g("MATH 136", ["MATH 126", "MATH 207"], ["MATH 126", "MATH 307"], ["MATH 126", "AMATH 351"], conc=True)
STATS = g("E E 391", "IND E 315", "MATH 394", "STAT 394", "STAT 390")
LINALG = g("MATH 136", "MATH 208", "AMATH 352")
PROG = g("E E 241", "CSE 163")

course("E E 200", "Undergraduate Research Exploration Seminar", 1,
       "Weekly seminar where researchers present work, connecting students with EE research.",
       "None listed.", notes="Credit/no-credit.")
course("E E 201", "Computer Hardware Skills", 2,
       "Hands-on lab: circuit building, microcontrollers, soldering, sensors, and EE careers.",
       "CSE 122, CSE 123, CSE 142, or CSE 143, any of which may be taken concurrently.",
       [g("CSE 122", "CSE 123", "CSE 142", "CSE 143", conc=True)], offered="AWSp")
course("E E 205", "Introduction to Signal Conditioning", 4,
       "Analog circuits that connect sensors to digital systems, for non-EE majors.",
       "Either MATH 126 or MATH 136; and either PHYS 122 or PHYS 142.",
       [g("MATH 126", "MATH 136"), g("PHYS 122", "PHYS 142")], offered="W")
course("E E 215", "Fundamentals of Electrical Engineering", 4,
       "Basic circuit and systems concepts, component models, and first/second-order circuit equations.",
       "Either MATH 136, or MATH 126 and either MATH 207, MATH 307, or AMATH 351, any of which may be taken concurrently; and either PHYS 122 or PHYS 142.",
       [EE_CORE_215_MATH, g("PHYS 122", "PHYS 142")])
course("E E 233", "Circuit Theory", 5,
       "Sinusoidal circuit analysis with phasors, frequency response, power, and two-port networks, with lab.",
       "E E 215.", [g("E E 215")])
course("E E 241", "Programming for Signal and Information Processing Applications", 2,
       "Programming for signal and information processing: data types, data packages, and visualization.",
       "Either CSE 122, CSE 123, CSE 142, CSE 143, or CSE 160.",
       [g("CSE 122", "CSE 123", "CSE 142", "CSE 143", "CSE 160")])
course("E E 242", "Signals, Systems, and Data I", 5,
       "Continuous- and discrete-time signals and systems, convolution, Fourier methods, and filters, with lab.",
       "Either MATH 135, MATH 207, or AMATH 351, any of which may be taken concurrently; and either E E 241 or CSE 163.",
       [g("MATH 135", "MATH 207", "AMATH 351", conc=True), PROG], offered="AWSp")
course("E E 271", "Digital Circuits and Systems", 5,
       "Boolean logic, combinational and sequential circuits, and digital computer design, with weekly labs.",
       "Either CSE 121, CSE 122, CSE 123, CSE 142, or CSE 143.",
       [g("CSE 121", "CSE 122", "CSE 123", "CSE 142", "CSE 143")])
course("E E 280", "Exploring Devices", 4,
       "Electronic and photonic devices in everyday products and the physics used to model them.",
       "E E 215, which may be taken concurrently; and either PHYS 122 or PHYS 142; recommended: Python or Matlab programming and Linux.",
       [g("E E 215", conc=True), g("PHYS 122", "PHYS 142")], offered="AWSp")
course("E E 299", "Introductory Topics in Electrical Engineering", 1,
       "New and experimental approaches to basic electrical engineering.", "None listed.", credits_max=5)
course("E E 331", "Devices and Circuits", 4,
       "Diode and FET circuits with emphasis on large-signal and digital logic behavior, with labs.",
       "E E 215 and E E 280.", [g("E E 215"), g("E E 280")], offered="AWSp")
course("E E 332", "Devices and Circuits: Analog", 5,
       "FET physics and small-signal analog amplifier design with lab instruments and CAD tools.",
       "E E 233 and E E 280; recommended: E E 331.", [g("E E 233"), g("E E 280")], offered="ASp", recommended="E E 331")
course("E E 333", "Analog Embedded Systems", 5,
       "Analog circuit design: op amps, differential amplifiers, active filters, and regulators.",
       "E E 233; E E 242; and either E E 280 or E E 331.", [g("E E 233"), g("E E 242"), g("E E 280", "E E 331")])
course("E E 342", "Signals, Systems, and Data II", 4,
       "Laplace and z-transforms, sampling, FFT, multirate processing, and machine learning applications.",
       "E E 242.", [g("E E 242")])
course("E E 344", "Data-Driven Modeling and Machine Learning", 4,
       "Practical supervised and unsupervised learning, neural networks, and reinforcement learning.",
       "Either MATH 126 or MATH 136; and either E E 241 or CSE 163.", [g("MATH 126", "MATH 136"), PROG])
course("E E 345", "Introduction to Foundations of Machine Learning", 4,
       "Mathematical foundations of machine learning: linear algebra, regression, classification, clustering.",
       "Either MATH 136, MATH 208, or AMATH 352; and either E E 241 or CSE 163.", [LINALG, PROG])
course("E E 347", "Introduction to Robotics and Control Systems", 5,
       "Robot modeling, kinematics, control, sensing, navigation, and path planning, with labs.",
       "E E 241 or CSE 163; and either MATH 136, MATH 208, or AMATH 352.", [PROG, LINALG])
course("E E 351", "Energy Systems", 5,
       "Electric generation, transmission, and use, plus power electronics, renewables, and the grid.",
       "A minimum grade of 1.0 in E E 215.", [g("E E 215", grade=1.0)])
course("E E 361", "Applied Electromagnetics", 5,
       "Maxwell's equations, plane waves, guided waves, transmission lines, and electrostatics.",
       "A minimum grade of 1.0 in E E 215; and either PHYS 123 or PHYS 143.",
       [g("E E 215", grade=1.0), g("PHYS 123", "PHYS 143")])
course("E E 371", "Design of Digital Circuits and Systems", 5,
       "Verilog modeling of complex digital systems, signal integrity, and power management.",
       "Either E E 205 or E E 215; either E E 271 or CSE 369.", [g("E E 205", "E E 215"), g("E E 271", "CSE 369")],
       notes="Offered jointly with CSE 371.")
course("E E 391", "Probability for Information and Communication Engineering", 4,
       "Probability for signal processing, data science, and communications, with Python labs.",
       "E E 242; and MATH 126 or MATH 136.", [g("E E 242"), g("MATH 126", "MATH 136")])
course("E E 393", "Advanced Technical Communication", 4,
       "Practical and persuasive technical writing and presentations for varied audiences.", "None listed.")
course("E E 397", "Sex and Gender in Engineering", 3,
       "Professional issues faced by women and LGBTQ+ people in engineering workplaces.", "None listed.")
course("E E 398", "Introduction to Professional Issues", 1,
       "Career topics: salaries, advanced degrees, engineering ethics, patents, and the global market.", "None listed.")
course("E E 399", "Special Topics in Electrical Engineering", 1,
       "New and experimental approaches to current electrical engineering problems.", "None listed.", credits_max=5)
course("E E 400", "Advanced Topics in Electrical Engineering", 1,
       "Advanced elective topics not part of the established curriculum.", "None listed.", credits_max=5)
course("E E 406", "Teaching Engineering", 3,
       "Inclusive, effective teaching methods for engineering and STEM.", "None listed.")
course("E E 416", "Random Signals for Communications and Signal Processing", 4,
       "Probability and random processes in communications; statistical filter design.",
       "E E 242 or E E 341; and STAT 390, MATH 394/STAT 394, or IND E 315.",
       [g("E E 242", "E E 341"), g("STAT 390", "MATH 394", "STAT 394", "IND E 315")])
course("E E 417", "Modern Wireless Communications", 4,
       "Modulation, receiver design, error control, fading, and WiFi/WiMax.", "E E 416.", [g("E E 416")])
course("E E 418", "Network Security and Cryptography", 4,
       "Cryptographic fundamentals and protocols that secure networks and communications.",
       "CSE 163 or E E 241; MATH 136 (or MATH 126 with MATH 208 or AMATH 352); E E 391, IND E 315, MATH 394/STAT 394, or STAT 390.",
       [PROG, g("MATH 136", ["MATH 126", "MATH 208"], ["MATH 126", "AMATH 352"]), STATS])
course("E E 419", "Introduction to Computer-Communication Networks", 4,
       "Network architectures, protocols, routing, congestion control, and transport protocols.",
       "E E 391, IND E 315, or STAT 390; E E 241 or CSE 163.", [g("E E 391", "IND E 315", "STAT 390"), PROG], offered="ASp")
course("E E 420", "Design in Communications", 4,
       "Team communications design projects with reports and presentations.",
       "Minimum grade 1.0 in E E 417 (may be concurrent).", [g("E E 417", conc=True, grade=1.0)])
course("E E 421", "Quantum Mechanics for Engineers", 3,
       "Quantum theory applied to nanomaterials: quantization, band structure, density of states.",
       "MATH 135, MATH 207, MATH 307, or AMATH 351.", [g("MATH 135", "MATH 207", "MATH 307", "AMATH 351")])
course("E E 423", "Introduction to Synthetic Biology", 3,
       "Mathematical models of gene regulation and design of genetic circuits.",
       "MATH 136, 207, 307, AMATH 351, or CSE 311; and MATH 208, 308, or AMATH 352.",
       [g("MATH 136", "MATH 207", "MATH 307", "AMATH 351", "CSE 311"), g("MATH 208", "MATH 308", "AMATH 352", "MATH 136")],
       notes="Offered jointly with BIOEN/CHEM E/CSE.")
course("E E 424", "Advanced Systems and Synthetic Biology", 3,
       "Kinetics, modeling, control, and signaling in biological systems.", "E E 423 or equivalent.", [g("E E 423")])
course("E E 425", "Laboratory Methods in Synthetic Biology", 4,
       "Build and evaluate transgenic bacteria from genetic parts.",
       "E E 423 or equivalent; CHEM 142, 143, or 145.", [g("E E 423"), g("CHEM 142", "CHEM 143", "CHEM 145")])
course("E E 435", "Linear Integrated Circuits", 5,
       "Linear IC analysis and design: amplifiers, op-amp architectures, feedback, and compensation.",
       "E E 332 and E E 333; recommended: E E 331 and E E 361.", [g("E E 332"), g("E E 333")], offered="A")
course("E E 436", "Integrated Systems Capstone I", 5,
       "Team design of analog/mixed-signal systems-on-chip, leading toward tapeout (part 1 of 2).",
       "E E 435; recommended: E E 331 and E E 361.", [g("E E 435")], offered="W")
course("E E 437", "Integrated Systems Capstone II", 5,
       "Continues the chip design project through verification, tapeout, and fabrication (part 2 of 2).",
       "E E 436.", [g("E E 436")], offered="Sp")
course("E E 440", "Introduction to Digital Imaging Systems", 4,
       "Image representation, filtering, restoration, transforms, coding, and camera models.",
       "E E 341 or E E 342.", [g("E E 341", "E E 342")])
course("E E 442", "Digital Signals and Filtering", 3,
       "Sampling, z-transforms, digital filter design, and the FFT.",
       "Minimum grade 1.0 in E E 341 or E E 342.", [g("E E 341", "E E 342", grade=1.0)])
course("E E 443", "Machine Learning for Signal Processing Applications", 4,
       "Machine and deep learning for signal, image, and video processing.",
       "Minimum grade 1.0 in E E 242; MATH 136 (or MATH 126 with MATH 208 or AMATH 352); E E 391, IND E 315, MATH 394/STAT 394, or STAT 390.",
       [g("E E 242", grade=1.0), g("MATH 136", ["MATH 126", "MATH 208"], ["MATH 126", "AMATH 352"]), STATS])
course("E E 445", "Fundamentals of Optimization and Machine Learning", 4,
       "Convex optimization and its use in regression and classification models.", "E E 345.", [g("E E 345")])
course("E E 446", "Tiny Machine Learning for Ultra Low-Power Edge Computing", 4,
       "Designing and deploying compact ML models on microcontrollers and sensors.",
       "E E 242; AMATH 352, MATH 136, or MATH 208; IND E 315, MATH 394/STAT 394, STAT 390, or E E 391; recommended: E E 344.",
       [g("E E 242"), LINALG, STATS], offered="Sp", recommended="E E 344")
course("E E 447", "Control System Analysis I", 4,
       "Feedback stability analysis, Bode and Nichols design methods, and state variables.",
       "E E 233; E E 235 or E E 242; MATH 136, 208, or 308.",
       [g("E E 233"), g("E E 235", "E E 242"), g("MATH 136", "MATH 208", "MATH 308")])
course("E E 448", "Control Systems Laboratory", 4,
       "Control design applied to electromechanical systems such as DC motors.", "E E 447.", [g("E E 447")], offered="W")
course("E E 449", "Robotics and Controls Capstone", 4,
       "Team project building and testing robotic hardware with feedback control.", "E E 447.", [g("E E 447")], offered="Sp")
course("E E 451", "Wind Energy", 4,
       "Wind energy operation, generators and converters, and grid impacts.", "E E 351.", [g("E E 351")],
       notes="Offered in odd years.")
course("E E 452", "Power Electronics Design", 5,
       "Switching devices, converter circuits, magnetics design, and converter control.",
       "E E 331 and E E 351; recommended: E E 361.", [g("E E 331"), g("E E 351")])
course("E E 453", "Electric Drives", 5,
       "Motor speed-torque characteristics and speed control with solid-state drives.",
       "Minimum grade 1.0 in E E 452 and in E E 458.", [g("E E 452", grade=1.0), g("E E 458", grade=1.0)])
course("E E 454", "Power System Analysis", 4,
       "Symmetrical components, line parameters, and power flow.", "Minimum grade 1.0 in E E 351.", [g("E E 351", grade=1.0)])
course("E E 455", "Power System Dynamics and Protection", 4,
       "Fault analysis and stability of balanced and unbalanced power networks.",
       "Minimum grade 1.0 in E E 351.", [g("E E 351", grade=1.0)])
course("E E 456", "Computer-Aided Design in Power Systems", 4,
       "Power system design projects using existing software.",
       "Minimum grade 1.0 in E E 454 or E E 455.", [g("E E 454", "E E 455", grade=1.0)])
course("E E 457", "Electric Energy Distribution Systems", 4,
       "Distribution network analysis and design, substations, transformers, and reliability.",
       "Minimum grade 1.0 in E E 351.", [g("E E 351", grade=1.0)])
course("E E 458", "Power Electronics Controls", 5,
       "Closed-loop control of power converters using averaged and small-signal models.",
       "E E 447 and E E 452.", [g("E E 447"), g("E E 452")])
course("E E 460", "Neural Engineering", 3,
       "Neurobiology, neural recording and stimulation, brain-machine interfaces, and neuroethics.",
       "BIOL 130, 162, or 220; MATH 208, AMATH 301, or AMATH 352.",
       [g("BIOL 130", "BIOL 162", "BIOL 220"), g("MATH 208", "AMATH 301", "AMATH 352")], offered="A")
course("E E 461", "Neural Engineering Tech Studio", 4,
       "Team design and presentation of a neural engineering prototype.", "BIOEN 460/E E 460.",
       [g("E E 460", "BIOEN 460")], notes="Offered jointly with BIOEN 461.")
course("E E 462", "Electromagnetics I: Microwave Engineering", 4,
       "Microwave transmission lines, waveguides, resonators, and layered media.",
       "Minimum grade 1.0 in E E 361.", [g("E E 361", grade=1.0)])
course("E E 463", "Microwave Electronic Design", 4,
       "Microwave circuit design with S-parameters, measurement, CAD, and an amplifier build.",
       "E E 361; E E 332 (may be concurrent).", [g("E E 361"), g("E E 332", conc=True)])
course("E E 464", "Antennas: Analysis and Design", 4,
       "Radiation patterns, directivity, impedance, arrays, and horn and reflector antennas.",
       "Minimum grade 1.0 in E E 361.", [g("E E 361", grade=1.0)])
course("E E 465", "Network and Web Security", 4,
       "Network and web security principles, attacks, defenses, and protocol weaknesses.",
       "CSE 163 or E E 241; E E 418; recommended: E E 419.", [PROG, g("E E 418")], recommended="E E 419")
course("E E 466", "Neural Computation and Engineering Laboratory", 4,
       "Neural recording and quantitative analysis techniques.",
       "BIOL 130, 162, 220, or AMATH 342; MATH 208, AMATH 301, or AMATH 352.",
       [g("BIOL 130", "BIOL 162", "BIOL 220", "AMATH 342"), g("MATH 208", "AMATH 301", "AMATH 352")])
course("E E 467", "Machine Learning for Cybersecurity", 4,
       "Machine learning for anomaly detection, spam detection, and adversarial inputs.",
       "CSE 163 or E E 241; AMATH 352, MATH 208, 308, or 136; IND E 315, MATH 394/STAT 394, or STAT 390; recommended: E E 445.",
       [PROG, g("AMATH 352", "MATH 208", "MATH 308", "MATH 136"), g("IND E 315", "MATH 394", "STAT 394", "STAT 390")],
       recommended="E E 445")
course("E E 468", "Software and Embedded Systems Security", 4,
       "Security principles and tools for software, embedded systems, and their networks.",
       "E E 241 or CSE 163; recommended: E E 469/CSE 469 or E E 472.", [PROG])
course("E E 469", "Computer Architecture I", 5,
       "Assembly language, processor organization, arithmetic, memory systems, and caching.",
       "E E 271 or CSE 369; CSE 123 or CSE 143.", [g("E E 271", "CSE 369"), g("CSE 123", "CSE 143")],
       notes="Offered jointly with CSE 469.")
course("E E 470", "Computer Architecture II", 4,
       "Instruction- and thread-level parallelism, cache coherence, and GPU design.",
       "CSE 469 or E E 469.", [g("E E 469", "CSE 469")], notes="Offered jointly with CSE 470.")
course("E E 474", "Introduction to Embedded Systems", 4,
       "Designing and testing real-time embedded software on a microcontroller.",
       "CSE 123 or CSE 143.", [g("CSE 123", "CSE 143")], offered="AWSpS", notes="Offered jointly with CSE 474.")
course("E E 475", "Embedded Systems Capstone", 5,
       "Prototype a substantial project combining hardware, software, and communications.",
       "E E 271 or CSE 369; E E 472 or CSE 474/E E 474.", [g("E E 271", "CSE 369"), g("E E 472", "E E 474", "CSE 474")],
       notes="Offered jointly with CSE 475.")
course("E E 476", "Digital VLSI: Transistors to Gates", 5,
       "CMOS logic design, delay and power analysis, and IC layout.",
       "E E 215; E E 271 or CSE 369; recommended: basic circuit theory.", [g("E E 215"), g("E E 271", "CSE 369")], offered="AWSp")
course("E E 477", "Digital VLSI: Gates to Systems", 5,
       "Memory and datapath design in static and dynamic CMOS with industry CAD tools.",
       "E E 469/CSE 469.", [g("E E 469", "CSE 469")], offered="W")
course("E E 478", "Capstone Integrated Digital Design Projects", 5,
       "High-performance or low-energy IC design: wires, timing, clocking, and low-power design.",
       "E E 476 and E E 477.", [g("E E 476"), g("E E 477")], offered="Sp")
course("E E 482", "Semiconductor Devices", 4,
       "Diodes, LEDs, solar cells, photodetectors, and MOSFETs via carrier transport.",
       "E E 280, E E 331, MSE 351, or PHYS 324; MATH 135, 207, or AMATH 351.",
       [g("E E 280", "E E 331", "MSE 351", "PHYS 324"), g("MATH 135", "MATH 207", "AMATH 351")], offered="A")
course("E E 484", "Sensors and Sensor Systems", 4,
       "Optical and solid-state chemical and physical sensors and their applications.", "E E 331.", [g("E E 331")])
course("E E 486", "Fundamentals of Integrated Circuit Technology", 3,
       "IC fabrication: deposition, diffusion, ion implantation, oxidation, and photoresists.",
       "E E 331 or MSE 351.", [g("E E 331", "MSE 351")], offered="AW", notes="Offered jointly with MSE 486.")
course("E E 487", "Introduction to Photonics", 4,
       "Light as electromagnetic waves: interference, diffraction, polarization, and waveguides.",
       "E E 361, PHYS 123, or PHYS 143.", [g("E E 361", "PHYS 123", "PHYS 143")])
course("E E 488", "Advanced Photonics", 4,
       "Optical resonance, quantum properties of light, amplification, lasers, and photodetection.",
       "E E 485 or E E 487.", [g("E E 485", "E E 487")])
course("E E 489", "Electronic-Photonic Integrated Systems", 4,
       "Integrating electronic and photonic technologies in large-scale system design.",
       "E E 331, E E 332, or E E 487.", [g("E E 331", "E E 332", "E E 487")])
course("E E 490", "Reading and Research", 1,
       "Independent reading and research supervised by an E E faculty member.",
       "Supervision by an E E faculty member.", credits_max=5,
       notes="Credit/no-credit; counts only as free elective credit for BSECE.")
course("E E 491", "Undergraduate Seminar", 1, "Departmental colloquium seminar.", "None listed.",
       notes="Credit/no-credit; max 2 credits. Approved seminar for electives (max 2 seminar credits).")
course("E E 492", "Electrical Engineering Leadership Seminar", 1, "Leadership seminar for EE students.", "None listed.",
       notes="Credit/no-credit. Approved seminar for electives (max 2 seminar credits).")
course("E E 496", "Engineering Entrepreneurial Systems and Design", 2,
       "Entrepreneurial engineering systems and design.", "None listed.")
course("E E 497", "Engineering Entrepreneurial Capstone", 4,
       "Entrepreneurial capstone (part 1 of 2).", "None listed.")
course("E E 498", "Engineering Entrepreneurial Capstone", 4,
       "Entrepreneurial capstone (part 2 of 2).", "E E 497.", [g("E E 497")])
course("E E 499", "Undergraduate Research and Special Projects", 1,
       "Undergraduate research and special projects.", "None listed.", credits_max=5,
       notes="Max 6 credits count toward Advanced ECE Electives (max 6 combined with ENGR 321).")

courses = {"source": "UW course catalog (washington.edu/students/crscat), collected " + CHECKED,
           "note": "Descriptions are short summaries. Prerequisite text is from the catalog; always confirm in MyPlan.",
           "courses": C}
(OUT / "ece_courses.json").write_text(json.dumps(courses, indent=2) + "\n")

# ---------------- Requirements ----------------
R = lambda **k: k
req = {
    "program": "B.S. Electrical and Computer Engineering (BSECE), UW Seattle",
    "applies_to": "Engineering Undeclared (ENGRUD) students who entered Autumn 2026; major rules for students admitted Autumn 2025 or later",
    "total_credits": 180,
    "sources": [
        "https://www.engr.washington.edu/current/academics/4-year-plans/ece-degree-requirements (updated 2026-10-14)",
        "https://www.ece.uw.edu/academics/bachelor-of-science/bsece/degree-requirements/",
    ],
    "source_checked": CHECKED,
    "placement": {
        "label": "Placement into ECE (Engineering Undeclared students)",
        "deadline": "Placement decision July 15 after the first year",
        "min_grade_note": "ECE's audit lists a minimum grade of 2.0 in each placement course.",
        "items": [
            R(id="engr101", label="ENGR 101", type="one_of", courses=["ENGR 101"]),
            R(id="calc1", label="MATH 124 (or MATH 134)", type="one_of", courses=["MATH 124", "MATH 134"], min_grade=2.0),
            R(id="calc2", label="MATH 125 (or MATH 135)", type="one_of", courses=["MATH 125", "MATH 135"], min_grade=2.0),
            R(id="calc3", label="MATH 126 (or MATH 136)", type="one_of", courses=["MATH 126", "MATH 136"], min_grade=2.0),
            R(id="chem", label="CHEM 142 (or CHEM 143/145)", type="one_of", courses=["CHEM 142", "CHEM 143", "CHEM 145"], min_grade=2.0),
            R(id="phys1", label="PHYS 121 (or PHYS 141)", type="one_of", courses=["PHYS 121", "PHYS 141"], min_grade=2.0),
            R(id="comp", label="English Composition", type="category", category="english_comp", known_courses=["ENGL 131"]),
            R(id="pick", label="One of CSE 121, CSE 122, CSE 123, PHYS 122, PHYS 123", type="one_of",
              courses=["CSE 121", "CSE 122", "CSE 123", "PHYS 122", "PHYS 123", "PHYS 142", "PHYS 143"], min_grade=2.0),
        ],
    },
    "graduation": [
        {"group": "E-FIG", "items": [
            R(id="efig", label="ENGR 101 and GEN ST 199", type="all", courses=["ENGR 101", "GEN ST 199"])]},
        {"group": "Mathematics (24-27 cr)", "items": [
            R(id="calc", label="MATH 124, 125, 126 (or honors MATH 134, 135, 136)", type="sequence",
              options=[["MATH 124", "MATH 125", "MATH 126"], ["MATH 134", "MATH 135", "MATH 136"]]),
            R(id="diffeq", label="MATH 207 or AMATH 351", type="one_of", courses=["MATH 207", "AMATH 351"]),
            R(id="linalg", label="MATH 208 or AMATH 352", type="one_of", courses=["MATH 208", "AMATH 352"]),
            R(id="stats", label="IND E 315 or STAT 390", type="one_of", courses=["IND E 315", "STAT 390"])]},
        {"group": "Sciences (19-20 cr)", "items": [
            R(id="chem142", label="CHEM 142", type="one_of", courses=["CHEM 142", "CHEM 143", "CHEM 145"]),
            R(id="phys121", label="PHYS 121", type="one_of", courses=["PHYS 121", "PHYS 141"]),
            R(id="phys122", label="PHYS 122", type="one_of", courses=["PHYS 122", "PHYS 142"]),
            R(id="sci_pick", label="One of BIOL 130, BIOL 220, MATH 224, PHYS 123", type="one_of",
              courses=["PHYS 123", "PHYS 143", "MATH 224", "BIOL 130", "BIOL 220"])]},
        {"group": "Programming (min 2.0)", "items": [
            R(id="prog", label="CSE 123 or CSE 143", type="one_of", courses=["CSE 123", "CSE 143"], min_grade=2.0)]},
        {"group": "ECE Core (min 2.0 each)", "items": [
            R(id="ee201", label="E E 201", type="one_of", courses=["E E 201"], min_grade=2.0),
            R(id="ee215", label="E E 215", type="one_of", courses=["E E 215"], min_grade=2.0),
            R(id="ee241", label="E E 241 or CSE 163", type="one_of", courses=["E E 241", "CSE 163"], min_grade=2.0),
            R(id="ee242", label="E E 242", type="one_of", courses=["E E 242"], min_grade=2.0),
            R(id="ee271", label="E E 271", type="one_of", courses=["E E 271"], min_grade=2.0),
            R(id="ee280", label="E E 280", type="one_of", courses=["E E 280"], min_grade=2.0)]},
        {"group": "Written communication and general education", "items": [
            R(id="comp", label="English Composition (5 cr)", type="category", category="english_comp", known_courses=["ENGL 131"]),
            R(id="ee393", label="E E 393 Advanced Technical Communication (or department-approved alternative)", type="one_of",
              courses=["E E 393"], min_grade=1.0),
            R(id="writing", label="Additional writing (3 cr)", type="category", category="W", credits=3),
            R(id="ah", label="Arts & Humanities (10 cr)", type="category", category="A&H", credits=10),
            R(id="ssc", label="Social Sciences (10 cr)", type="category", category="SSc", credits=10),
            R(id="ah_ssc", label="Additional A&H or SSc (4 cr)", type="category", category="A&H or SSc", credits=4),
            R(id="div", label="Diversity (5 cr)", type="category", category="DIV", credits=5),
            R(id="nsc45", label="Natural sciences to reach 45 cr (approved list; see adviser)", type="advisor")]},
        {"group": "Advanced ECE Electives (39 cr, min 1.0 each)", "items": [
            R(id="prof", label="Professional Issues (1-4 cr)", type="one_of", courses=["E E 397", "E E 398", "E E 406", "E E 418"]),
            R(id="electives", label="300- and 400-level E E courses to reach 39 credits", type="electives", credits=39,
              rules=["At least 20 credits at the 400 level",
                     "Max 2 credits of seminars (E E 491, E E 492)",
                     "Max 6 credits of E E 499",
                     "E E 233, CSE 373, CSE 374, and ENGR 321 may also count (ENGR 321 max 4 credits)",
                     "Max 6 credits combined of ENGR 321 and E E 499",
                     "E E 393 and capstone courses do not count",
                     "E E 490 counts only as a free elective"])]},
        {"group": "Capstone (4-8 cr, min 1.0)", "items": [
            R(id="capstone", label="One approved capstone (complete every course in a sequence)", type="sequence",
              options=[["E E 436", "E E 437"], ["E E 449"], ["E E 461"], ["E E 475"], ["E E 478"], ["E E 497", "E E 498"]])]},
    ],
    "grade_rules": {
        "ECE core and programming": 2.0,
        "Advanced technical communication, capstone, electives": 1.0,
        "Other requirements": 0.7,
        "Major GPA": "Minimum 2.0 cumulative in courses applied to the major; no grade below 1.0",
        "S/NS": "Courses used for requirements must be graded",
    },
    "older_rules_note": "Students admitted before Autumn 2025 have 36 elective credits with the capstone counted inside them. This app uses the Autumn 2025+ rules.",
}
(OUT / "ece_requirements.json").write_text(json.dumps(req, indent=2) + "\n")

# ---------------- Sample plan ----------------
Q = lambda *items: [{"item": i, "credits": c} for i, c in items]
plan = {
    "source": "https://www.engr.washington.edu/current/academics/4-year-plans/ece-degree-requirements (updated 2026-10-14)",
    "note": "Sample plan for ENGRUD students; students build their own plan with an adviser.",
    "years": [
        {"year": 1, "autumn": Q(("MATH 124", 5), ("CHEM 142", 5), ("ENGR 101 & GEN ST 199", 2), ("A&H / SSc", 5)),
         "winter": Q(("MATH 125", 5), ("English Composition", 5), ("CSE 121", 4)),
         "spring": Q(("MATH 126", 5), ("PHYS 121", 5), ("DIV", 5))},
        {"year": 2, "autumn": Q(("PHYS 122", 5), ("MATH 207", 4), ("CSE 122", 4), ("Writing", 3)),
         "winter": Q(("MATH 208", 4), ("E E 215", 4), ("Free elective", 2), ("CSE 123", 4)),
         "spring": Q(("E E 280", 4), ("E E 241", 2), ("Free elective", 3), ("A&H / SSc", 5))},
        {"year": 3, "autumn": Q(("E E 242", 5), ("E E 271", 5), ("IND E 315", 3), ("Free elective", 2)),
         "winter": Q(("E E 201", 2), ("E E 393", 4), ("Advanced ECE Elective", 5), ("Additional approved NSc course", 5)),
         "spring": Q(("Advanced ECE Elective", 4), ("Advanced ECE Elective", 4), ("A&H / SSc", 4), ("Free elective", 3))},
        {"year": 4, "autumn": Q(("Advanced ECE Elective", 5), ("Advanced ECE Elective", 5), ("Advanced ECE Elective (Professional Issues)", 1), ("A&H / SSc", 5)),
         "winter": Q(("Capstone", 4), ("Advanced ECE Elective", 5), ("Advanced ECE Elective", 5)),
         "spring": Q(("Capstone", 4), ("Advanced ECE Elective", 5), ("A&H / SSc", 5))},
    ],
}
(OUT / "ece_sample_plan.json").write_text(json.dumps(plan, indent=2) + "\n")
print(f"wrote {len(C)} courses to {OUT}")
