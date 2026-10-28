# language: Python 3.10+, file: digital_closet.py
# run: py -m streamlit run digital_closet.py

import streamlit as st
from PIL import Image
import json
import os
from datetime import datetime

st.set_page_config(page_title="Digital Closet", page_icon="👗", layout="wide")
st.title("👗 Digital Closet")
st.caption("Upload your clothes → ask for an outfit → get suggestions from what you already own.")

# ─────────────────────────────────────────────
# STORAGE
# ─────────────────────────────────────────────
CLOSET_FILE = "closet.json"
UPLOAD_DIR = "closet_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def load_closet():
    if os.path.exists(CLOSET_FILE):
        with open(CLOSET_FILE, "r") as f:
            return json.load(f)
    return []

def save_closet(items):
    with open(CLOSET_FILE, "w") as f:
        json.dump(items, f, indent=2)

if "closet" not in st.session_state:
    st.session_state.closet = load_closet()

# ─────────────────────────────────────────────
# SIDEBAR — ADD ITEM
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("Add to Closet")
    uploaded = st.file_uploader("Photo of the item", type=["jpg", "jpeg", "png"])
    name = st.text_input("Name / description", placeholder="black leather jacket")
    category = st.selectbox("Category", [
        "Top", "Bottom", "Dress", "Outerwear", "Shoes", "Accessory", "Bag", "Other"
    ])
    color = st.text_input("Color", placeholder="black")
    season = st.multiselect("Season", ["Spring", "Summer", "Fall", "Winter", "All"])
    style_tags = st.multiselect("Style tags", [
        "casual", "formal", "streetwear", "elegant", "sporty", "minimal", "vintage", "party"
    ])
    notes = st.text_area("Notes (optional)", height=60)

    if st.button("Add item", type="primary") and uploaded and name:
        img = Image.open(uploaded)
        fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name.replace(' ', '_')[:30]}.jpg"
        path = os.path.join(UPLOAD_DIR, fname)
        img.convert("RGB").save(path, quality=85)

        item = {
            "id": len(st.session_state.closet) + 1,
            "name": name,
            "category": category,
            "color": color.lower(),
            "season": season or ["All"],
            "tags": style_tags,
            "notes": notes,
            "image": path,
            "added": datetime.now().isoformat()
        }
        st.session_state.closet.append(item)
        save_closet(st.session_state.closet)
        st.success(f"Added: {name}")
        st.rerun()

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
tab1, tab2 = st.tabs(["My Closet", "Generate Outfit"])

with tab1:
    st.subheader(f"Your closet ({len(st.session_state.closet)} items)")
    if not st.session_state.closet:
        st.info("No items yet. Add some from the sidebar.")
    else:
        cols = st.columns(4)
        for i, item in enumerate(st.session_state.closet):
            with cols[i % 4]:
                if os.path.exists(item["image"]):
                    st.image(item["image"], use_container_width=True)
                st.markdown(f"**{item['name']}**")
                st.caption(f"{item['category']} · {item['color']} · {', '.join(item['tags'])}")
                if st.button("Remove", key=f"del_{item['id']}"):
                    st.session_state.closet = [x for x in st.session_state.closet if x["id"] != item["id"]]
                    save_closet(st.session_state.closet)
                    st.rerun()

with tab2:
    st.subheader("What do you need an outfit for?")
    occasion = st.text_input(
        "Describe the occasion / vibe / weather",
        placeholder="e.g. casual Friday at the office, rainy day, date night, concert, airport travel…"
    )
    must_include = st.text_input("Must include this item (optional)", placeholder="black leather jacket")
    prefer_colors = st.text_input("Prefer these colors (optional)", placeholder="black, white, navy")

    if st.button("Generate outfit", type="primary") and occasion:
        closet = st.session_state.closet
        if len(closet) < 2:
            st.warning("Add at least a couple of items first.")
        else:
            occasion_l = occasion.lower()
            prefer = [c.strip().lower() for c in prefer_colors.split(",") if c.strip()] if prefer_colors else []

            def score(item):
                s = 0
                text = (item["name"] + " " + " ".join(item["tags"]) + " " + item["notes"]).lower()
                for word in occasion_l.split():
                    if word in text or word in item["category"].lower():
                        s += 2
                if "formal" in occasion_l or "office" in occasion_l or "interview" in occasion_l:
                    if any(t in item["tags"] for t in ["formal", "elegant", "minimal"]):
                        s += 3
                if "casual" in occasion_l or "weekend" in occasion_l:
                    if any(t in item["tags"] for t in ["casual", "streetwear", "minimal"]):
                        s += 3
                if "party" in occasion_l or "date" in occasion_l or "night" in occasion_l:
                    if any(t in item["tags"] for t in ["party", "elegant", "streetwear"]):
                        s += 3
                if "rain" in occasion_l or "cold" in occasion_l or "winter" in occasion_l:
                    if item["category"] in ["Outerwear", "Shoes"] or "Winter" in item["season"]:
                        s += 2
                if prefer and item["color"] in prefer:
                    s += 2
                if must_include and must_include.lower() in item["name"].lower():
                    s += 10
                return s

            ranked = sorted(closet, key=score, reverse=True)

            outfit = []
            used_cats = set()
            for item in ranked:
                cat = item["category"]
                if cat not in used_cats and cat in ["Top", "Bottom", "Dress", "Outerwear", "Shoes", "Bag"]:
                    outfit.append(item)
                    used_cats.add(cat)
                if len(outfit) >= 4:
                    break
            if not outfit:
                outfit = ranked[:3]

            st.markdown("### Suggested outfit")
            st.write(f"**For:** {occasion}")
            cols = st.columns(min(len(outfit), 4))
            for i, item in enumerate(outfit):
                with cols[i]:
                    if os.path.exists(item["image"]):
                        st.image(item["image"], use_container_width=True)
                    st.markdown(f"**{item['name']}**")
                    st.caption(f"{item['category']} · {item['color']}")
