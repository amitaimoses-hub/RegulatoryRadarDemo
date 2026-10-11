# Offline note in README — summary

**What I changed:** I added one sentence to `README.md`: "The app can run offline using saved sample data." It sits on its own line, under the existing description.

**Why:** You asked for the README to say that the app can run offline using saved sample data.

**How it was tested:** This change is documentation only, so there was nothing to run. I read the change line by line to confirm that only that one sentence (and a blank line before it) was added. I also checked that only `README.md` went into the commit.

**Branch I ended on:** `docs/offline-sample-data-note`. I created it from an up-to-date `main` after pulling. No work was done on `main`.

**Committed:** Yes, one commit ("docs: note that the app can run offline with saved sample data"). It contains only `README.md`. The untracked `.env` file is still in the folder, but I didn't commit it because it may hold secrets.

**Pushed:** Yes. The branch `docs/offline-sample-data-note` is pushed to `origin` and set up to track it. `main` on the remote is unchanged.

**Pull request:** I couldn't open one because the `gh` tool isn't installed and there's no GitHub website. A teammate can open it from `docs/offline-sample-data-note` into `main` with this description:

> **What changed:** Added one sentence to `README.md` saying the app can run offline using saved sample data.
>
> **Why:** So readers know the app works without a network connection by using the saved sample data.
>
> **How it was tested:** This is a docs-only change. I reviewed the change to confirm that one sentence was added to `README.md` and nothing else changed. No code was touched.

**Merged:** No. A person should merge it after review and green CI.
