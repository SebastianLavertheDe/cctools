import json
import shlex
import subprocess
from pathlib import Path


X_CURL_FILE = Path(__file__).parent / "curl.txt"


def execute_curl_from_file() -> subprocess.CompletedProcess:
    with open(X_CURL_FILE, "r", encoding="utf-8") as f:
        curl_content = f.read().strip()
    curl_cmd = curl_content.replace("\\\n", " ").replace("\\\r\n", " ")
    cmd_list = shlex.split(curl_cmd)
    return subprocess.run(cmd_list, capture_output=True, text=True, timeout=120)


if __name__ == "__main__":
    result = execute_curl_from_file()
    if result.returncode != 0:
        print("curl failed:", result.stderr)
        raise SystemExit(1)

    data = json.loads(result.stdout)
    instructions = (
        data.get("data", {})
        .get("home", {})
        .get("home_timeline_urt", {})
        .get("instructions", [])
    )
    tweets = []
    for instr in instructions:
        if instr.get("type") == "TimelineAddEntries":
            for entry in instr.get("entries", []):
                content = entry.get("content", {})
                if content.get("__typename") == "TimelineTimelineItem":
                    tweets.append(entry)

    print(f"Parsed {len(tweets)} timeline entries")
