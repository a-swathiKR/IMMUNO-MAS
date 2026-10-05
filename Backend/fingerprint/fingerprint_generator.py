import json
from pathlib import Path

from feature_extractor import generate_fingerprint


OUTPUT_FILE = (
    Path(__file__).resolve().parent
    / "behavioral_fingerprints.json"
)


def save_fingerprints():

    fingerprints = generate_fingerprint()

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            fingerprints,
            file,
            indent=4
        )

    print(
        f"Behavioral fingerprints saved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    save_fingerprints()