# Yuna K-Beauty Desk

Static GitHub Pages website for the Yuna K-Beauty channel, with preserved public documentation for the private K-Beauty API Test creator sandbox.

## Live site

https://k2postman.github.io/kbeauty-api-site/

## Local verification

```bash
python tests/verify_site.py
python tests/verify_qa_harness.py
python scripts/qa_site.py
```

The browser QA harness starts its own loopback server on an OS-assigned free port. For a manual preview, run `python -m http.server 8000 --bind 127.0.0.1` (or another open port) and open the printed local URL.

## Safety boundary

- No analytics or tracking scripts
- No forms, accounts, payments, or public API backend
- TikTok verification file remains at the repository root
- Terms and Privacy pages remain public
- Featured media is copied from the user's own public YouTube channel; provenance is recorded in `assets/PROVENANCE.md`
