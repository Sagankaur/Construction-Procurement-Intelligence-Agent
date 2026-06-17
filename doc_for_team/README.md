# SiteSage AI Documentation Pack

Use these files to explain SiteSage AI to teammates, mentors, judges, and hackathon reviewers.

## Recommended Reading Order

1. `brief.md` - short project summary and current scope.
2. `team_onboarding.md` - how team members should run, test, and navigate the project.
3. `team_work_division.md` - ownership split for the three-person hackathon team.
4. `technical_architecture.md` - how frontend, RAG, ML, SQLite, and alerts fit together.
5. `demo_script.md` - exact demo flow and questions to use.
6. `hackathon_pitch.md` - problem, solution, differentiators, and judging story.
7. `roadmap_risks.md` - known limitations, risks, and next build priorities.

## Current Source Layout

The working app is in:

```text
code/
  app.py
  pages/
  src/
  data/
  docs/
  tests/
  README.md
```

The documentation pack is in:

```text
doc/
```

## Quick Commands

Run tests:

```powershell
cd "C:\sagan ASUS\IIT\kaya\code"
$env:PYTHONDONTWRITEBYTECODE="1"
..\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Run app:

```powershell
cd "C:\sagan ASUS\IIT\kaya\code"
..\.venv\Scripts\python.exe -B -m streamlit run app.py
```

Open:

```text
http://localhost:8501
```
