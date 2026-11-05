"""Run the CoMET-RS pipeline on GitHub links, skipping repositories already extracted."""
import argparse
import json
import os
import time
from pathlib import Path

from app.layer_4.services.metadata_service import initialize, run_extraction

GITHUB_URLS_FILE = Path("data/github_urls.txt")
RESULTS_FILE = Path("data/training_metadata.json")
SCHEMA_NAME = "TrainingMaterial"
SCHEMA_CLASS = "TrainingMaterial"


def normalize(url):
    return url.strip().rstrip("/").removesuffix(".git").lower()


def save_json(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    os.replace(temporary, path)


def is_rate_limited(errors):
    return any("403" in str(error) or "429" in str(error) for error in errors.values())

def has_values(document):
    return any(not key.startswith("@") and value not in (None, [], "") for key, value in document.items())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub token")
    parser.add_argument("--limit", type=int, help="Process at most this many new repositories")
    args = parser.parse_args()

    urls = [line.strip() for line in GITHUB_URLS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = json.loads(RESULTS_FILE.read_text(encoding="utf-8")) if RESULTS_FILE.exists() else {}
    done = {normalize(url) for url in results}
    pending = [url for url in urls if normalize(url) not in done]
    if args.limit is not None:
        pending = pending[: args.limit]
    print(f"Repositories: {len(urls)}, already extracted: {len(urls) - len([u for u in urls if normalize(u) not in done])}, to do now: {len(pending)}")

    initialize()
    saved, failed = 0, []
    for index, url in enumerate(pending, start=1):
        result = run_extraction(
            repo_url=url,
            schema_name=SCHEMA_NAME,
            schema_class=SCHEMA_CLASS,
            access_token=args.token,
            with_enrichment=False,
            fairness_assessment=False,
        )
        errors = result.extraction_state.errors
        if errors:
            failed.append(url)
            print(f"[{index}/{len(pending)}] NOT saved, will retry next run: {url} ({len(errors)} errors)")
            for step_name, message in errors.items():
                print(f"    {step_name}: {message}")
            if is_rate_limited(errors):
                print("Stopping: GitHub refused the request, probably a rate limit. Run again later.")
                break
                
        elif not has_values(result.jsonld_document):
            print(f"Stopping: no metadata extracted for {url}. Check that the schema matches the plugins.")
            break
        else:
            results[url] = result.jsonld_document
            save_json(RESULTS_FILE, results)  # saved after every repository, so progress survives a crash
            saved += 1
            print(f"[{index}/{len(pending)}] Saved: {url}")
        time.sleep(1)

    print(f"Saved now: {saved}, failed: {len(failed)}, total saved: {len(results)}")


if __name__ == "__main__":
    main()