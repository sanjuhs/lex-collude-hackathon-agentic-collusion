# Research paper

- **Read:** [lexcollude-paper.pdf](lexcollude-paper.pdf)
- **Edit:** [lexcollude-paper.docx](lexcollude-paper.docx)
- **Plain-text manuscript:** [manuscript.md](manuscript.md)
- **Submission abstract:** [abstract.txt](abstract.txt)
- **Verified bibliographic metadata:** [sources.json](sources.json)

Author: **Sanjayprasad H S**. No institutional affiliation was supplied; “LexCollude project” identifies this project, not an employer or university.

The paper is generated from the official sprint DOCX template's style definitions and page geometry. Its instructional body is replaced, and the section structure is adapted as the template permits. The original downloaded template is preserved as `official-template.docx`.

Template source: https://docs.google.com/document/d/1Y5wd3VRbXU5N08BvAGiJUQTaWbMCSPjhzXsR-ozuehg/copy?usp=sharing

Official guidelines, checked 26 October 2026: https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25

The guidelines require a PDF using the template, at most eight main-text pages, a 150–250-word abstract, author details, and a Limitations and Dual-Use / Ethical Considerations appendix. The manuscript also discloses LLM assistance. The project has **not been submitted** by the agent.

To rebuild, first run `make research`, then `make paper`. PDF conversion needs LibreOffice's `soffice` executable; the cloud environment already provides it. The editable DOCX is preserved if PDF conversion fails. `scripts/build_paper.py` refuses a final paper unless both completed study cohorts are present. A local `--allow-partial` preview is explicitly a development aid and must not be submitted as final.

The author should review the paper's interpretations and author/affiliation details before submitting. The agent did not perform independent blinded human adjudication of coordination.
