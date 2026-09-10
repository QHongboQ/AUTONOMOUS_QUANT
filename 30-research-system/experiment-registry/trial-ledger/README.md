# AQ Trial Ledger runtime foundation

Standard-library SQLite foundation. Run from this directory with:

```powershell
py -V:Astral/CPython3.12.14 -m unittest discover -s tests -v
py -V:Astral/CPython3.12.14 -m compileall aq_trial_ledger tests
```

All tests create temporary databases and backups only. No production database path is configured.
