import random
import uuid
from datetime import datetime, timedelta
import json

def generate_events(n_users=50000, experiment_id="checkout_button_color"):
    events = []
    base_conversion_rate = 0.10
    treatment_lift = 0.15  # treatment tăng 15% so với control

    for _ in range(n_users):
        user_id = str(uuid.uuid4())
        variant = random.choice(["control", "treatment"])
        conversion_rate = base_conversion_rate * (
            1 + treatment_lift if variant == "treatment" else 1
        )

        assigned_at = datetime.now() - timedelta(days=random.randint(0, 14))

        # Assignment event
        events.append({
            "user_id": user_id,
            "experiment_id": experiment_id,
            "variant": variant,
            "event_type": "assignment",
            "event_value": None,
            "event_timestamp": assigned_at.isoformat(),
        })

        # Page view (luôn xảy ra)
        events.append({
            "user_id": user_id,
            "experiment_id": experiment_id,
            "variant": variant,
            "event_type": "page_view",
            "event_value": None,
            "event_timestamp": (assigned_at + timedelta(seconds=5)).isoformat(),
        })

        # Purchase (xác suất theo variant)
        if random.random() < conversion_rate:
            events.append({
                "user_id": user_id,
                "experiment_id": experiment_id,
                "variant": variant,
                "event_type": "purchase",
                "event_value": round(random.uniform(20, 200), 2),
                "event_timestamp": (assigned_at + timedelta(minutes=random.randint(1, 30))).isoformat(),
            })

    return events

if __name__ == "__main__":
    events = generate_events()
    with open("raw_events.json", "w") as f:
        json.dump(events, f)
    print(f"Generated {len(events)} events")