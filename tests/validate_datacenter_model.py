import yaml
from pathlib import Path

MODEL_PATH = Path("configs/datacenter_model.yaml")

def collect_topics(obj, topics):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "topic_template":
                topics.append(value)
            elif isinstance(value, str) and "/" in value:
                topics.append(value)
            else:
                collect_topics(value, topics)
    elif isinstance(obj, list):
        for item in obj:
            collect_topics(item, topics)

def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Missing file: {MODEL_PATH}")

    with MODEL_PATH.open("r", encoding="utf-8") as f:
        model = yaml.safe_load(f)

    assert "site" in model, "Missing site section"
    assert "systems" in model, "Missing systems section"
    assert "dashboards" in model, "Missing dashboards section"
    assert "thresholds" in model, "Missing thresholds section"

    topics = []
    collect_topics(model, topics)

    duplicated = sorted({t for t in topics if topics.count(t) > 1})

    print("✅ Datacenter model loaded")
    print(f"✅ Systems: {len(model['systems'])}")
    print(f"✅ Dashboards: {len(model['dashboards'])}")
    print(f"✅ Topics/templates found: {len(topics)}")

    if duplicated:
        print("⚠️ Duplicate topics found:")
        for t in duplicated:
            print(" -", t)
    else:
        print("✅ No duplicate topics detected")

if __name__ == "__main__":
    main()
