import os
import io
import base64
import yaml
from dotenv import load_dotenv
import streamlit as st
from PIL import Image
from openai import OpenAI
from types import SimpleNamespace
from typing import Dict, Any
from core.utils import Utility

# ---- Your existing modules ----
from core.model import Imagine
from core.prompt_store import init_db, save_prompt, get_recent_prompts

# =========================================================
# Setup
# =========================================================
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=API_KEY) if API_KEY else None

st.set_page_config(
    page_title="Imagine - Premium Napkin Generator", page_icon="🎨", layout="wide"
)
st.title("🎨 Premium Paper Napkin — Theme-led Generator")
st.caption(
    "Pick a theme, choose render settings, (optionally) add extra art direction."
)
init_db()

if not API_KEY:
    st.warning("Set OPENAI_API_KEY in your environment or .env file.", icon="⚠️")

if "recent_prompts" not in st.session_state:
    st.session_state.recent_prompts = []
if "prompt" not in st.session_state:
    st.session_state.prompt = ""

# st.session_state.recent_prompts = get_recent_prompts(limit=5)


# Load the string template with placeholders like {motif}, {background_treatment}, {extra}, etc.
NAPKIN_TEMPLATE = Utility.load_template()

# =========================================================
# Minimal Theme Presets (locked brief; user only chooses theme)
# =========================================================
THEMES_PRESETS_MIN: Dict[str, Dict[str, Any]] = {
    "🌸 Spring Garden Wedding": {
        "motif": "watercolor peony-and-lavender floral wreath",
        "background_treatment": "soft blush pastel wash",
        "illustration_style": "hand-painted watercolor with delicate linework",
        "botanical_motifs": "lavender sprigs, peonies, eucalyptus",
        "animal_motifs": "none",
        "rim_style": "scalloped rim with subtle gold foil edge",
        "background_library": "pastel wash, faint diagonal stripes",
        "base_tones": "blush pink, cream, ivory",
        "accent_colors": "sage green, lavender",
        "metallic_finish": "gold foil accents",
        "decorative_florals": "flowing natural sprigs",
        "decorative_icons": "tiny bows or petals (sparingly)",
        "border_style": "gold rim with sparse floral repeats",
        "finish_spec": "matte base with selective glossy floral highlights",
        "aspect": "square",
        "api_size": "1024x1024",
        "quality_hint": "hd",
        "typography_style": "calligraphic script",
        "typography_placement": "subtle rim placement",
        "typography_color": "metallic gold",
        "theme_notes": "Wedding elegance; keep palette airy and romantic.",
        "use_typography": "no",
        "typography_copy": "",
    },
    "🐇 Woodland Birthday": {
        "motif": "whimsical bunny illustration with floral sprigs",
        "background_treatment": "soft diagonal stripe",
        "illustration_style": "realistic sketch with soft watercolor fill",
        "botanical_motifs": "wildflowers, lavender",
        "animal_motifs": "bunny, small songbirds",
        "rim_style": "rounded rim with thin gold foil edge",
        "background_library": "soft stripes, pastel wash",
        "base_tones": "pastels—lavender, blush, cream",
        "accent_colors": "sunshine yellow, turquoise",
        "metallic_finish": "gold shimmer accents",
        "decorative_florals": "hand-painted sprigs",
        "decorative_icons": "stars and tiny bows",
        "border_style": "gold rim with tiny star repeats",
        "finish_spec": "matte with glossy highlights on motif",
        "aspect": "square",
        "api_size": "1024x1024",
        "quality_hint": "standard",
        "typography_style": "rounded friendly",
        "typography_placement": "small banner below motif",
        "typography_color": "deep green",
        "theme_notes": "Child-friendly but elegant; avoid clutter.",
        "use_typography": "no",
        "typography_copy": "",
    },
    "🦌 Festive Holiday": {
        "motif": "regal deer with holly vines and red berries",
        "background_treatment": "ivory with subtle gradient fade",
        "illustration_style": "detailed watercolor with precise linework",
        "botanical_motifs": "holly, evergreen sprigs",
        "animal_motifs": "deer, winter birds",
        "rim_style": "circular rim with bold gold foil",
        "background_library": "muted gradient, light pastel wash",
        "base_tones": "ivory, taupe",
        "accent_colors": "berry red, deep green",
        "metallic_finish": "rich gold foil",
        "decorative_florals": "holly sprigs",
        "decorative_icons": "snowflakes (minimal)",
        "border_style": "gold rim with holly berry repeats (very subtle)",
        "finish_spec": "glossy highlights on metallics, matte base",
        "aspect": "square",
        "api_size": "1024x1024",
        "quality_hint": "hd",
        "typography_style": "elegant calligraphy",
        "typography_placement": "integrated along the rim",
        "typography_color": "metallic gold or berry red",
        "theme_notes": "Premium holiday tone; emphasize contrast and foil.",
        "use_typography": "no",
        "typography_copy": "",
    },
    "✨ Luxury Dinner": {
        "motif": "minimalist geometric center medallion",
        "background_treatment": "deep charcoal black",
        "illustration_style": "modern vector with subtle bevel",
        "botanical_motifs": "none",
        "animal_motifs": "none",
        "rim_style": "precise thin gold rim",
        "background_library": "flat or micro-texture",
        "base_tones": "black, charcoal",
        "accent_colors": "gold only, minimal",
        "metallic_finish": "high-polish gold",
        "decorative_florals": "none",
        "decorative_icons": "none",
        "border_style": "gold rim, no repeats",
        "finish_spec": "glossy metallic on matte base",
        "aspect": "square",
        "api_size": "1024x1024",
        "quality_hint": "hd",
        "typography_style": "none",
        "typography_placement": "none",
        "typography_color": "gold",
        "theme_notes": "Keep ultra-minimal; rely on contrast and finish.",
        "use_typography": "no",
        "typography_copy": "",
    },
    "🌴 Tropical Party": {
        "motif": "palm leaves and hibiscus floral ring",
        "background_treatment": "turquoise wash with subtle grain",
        "illustration_style": "vibrant watercolor + vector clean-up",
        "botanical_motifs": "palm, monstera, hibiscus",
        "animal_motifs": "butterflies or tropical birds (sparingly)",
        "rim_style": "gold rim with sparse floral accents",
        "background_library": "pastel wash, subtle grain, soft stripes",
        "base_tones": "turquoise, ivory",
        "accent_colors": "sunshine yellow, berry red",
        "metallic_finish": "gold foil accents",
        "decorative_florals": "loose hand-painted leaves",
        "decorative_icons": "tiny stars (optional)",
        "border_style": "gold rim with tiny hibiscus repeats",
        "finish_spec": "matte base with selective glossy floral highlights",
        "aspect": "square",
        "api_size": "1024x1024",
        "quality_hint": "standard",
        "typography_style": "friendly rounded",
        "typography_placement": "subtle banner or lower rim",
        "typography_color": "gold or deep green",
        "theme_notes": "Lively and premium; avoid over-saturation.",
        "use_typography": "no",
        "typography_copy": "",
    },
}


# =========================================================
# Prompt builder helpers
# =========================================================
class _SafeDict(dict):
    def __missing__(self, key):
        return ""


def _safe_clean(d: Dict[str, Any]) -> Dict[str, str]:
    return {k: (str(v).strip() if v is not None else "") for k, v in d.items()}


def build_napkin_prompt(theme_key: str, extra: str) -> str:
    base = THEMES_PRESETS_MIN[theme_key].copy()
    base["theme_label"] = theme_key
    base["extra"] = extra.strip() if extra.strip() else "—"
    return " ".join(
        str(NAPKIN_TEMPLATE).format_map(_SafeDict(_safe_clean(base))).split()
    )


# =========================================================
# Layout: left (form/results) | right (recents)
# =========================================================
left, right = st.columns([6, 2], vertical_alignment="top")

with left:
    with st.form("gen"):
        st.markdown("### Design Theme")
        theme_key = st.selectbox("Theme", list(THEMES_PRESETS_MIN.keys()), index=0)

        st.markdown("### Render Settings")
        # Defaults come from theme preset; user can override here
        default_size = THEMES_PRESETS_MIN[theme_key]["api_size"]
        default_quality = THEMES_PRESETS_MIN[theme_key]["quality_hint"]

        r1, r2 = st.columns(2)
        with r1:
            size = st.selectbox(
                "Size",
                ["1024x1024", "1024x1792", "1792x1024"],
                index=(
                    ["1024x1024", "1024x1792", "1792x1024"].index(default_size)
                    if default_size in ["1024x1024", "1024x1792", "1792x1024"]
                    else 0
                ),
            )
        with r2:
            quality = st.selectbox(
                "Quality",
                ["standard", "hd"],
                index=(0 if default_quality == "standard" else 1),
            )

        st.markdown("### Extra Detail (optional)")
        extra = st.text_area(
            "Add any small tweaks (e.g., butterflies, warmer gold, softer stripes)",
            height=80,
        )

        submitted = st.form_submit_button("Generate", use_container_width=True)

    # Placeholder to render/clear results
    gallery = st.empty()

# Right: recent prompts (compact)
with right:
    """"""
    # st.subheader("Recent prompts")
    # try:
    #     scroll = st.container(height=320, border=False)
    # except TypeError:
    #     scroll = None

    # def render_recent_list(container):
    #     recents = st.session_state.recent_prompts
    #     if recents:
    #         for rp in recents:
    #             with container.container(border=True):
    #                 st.code(rp, language=None, wrap_lines=True, height=75)
    #     else:
    #         container.caption("No prompts yet.")

    # if scroll:
    #     render_recent_list(scroll)
    # else:
    #     st.caption("No prompts yet.")

# =========================================================
# Submit handler
# =========================================================
if submitted:
    if not client:
        st.info("OPENAI_API_KEY is not set. Please add it and try again.")
    else:
        final_prompt = build_napkin_prompt(theme_key, extra)

        # Save & refresh recents
        save_prompt(final_prompt)
        st.session_state.recent_prompts = get_recent_prompts(limit=5)

        with st.spinner("Generating..."):
            model_name = "dall-e-3"
            gen_kwargs = {"model": model_name, "prompt": final_prompt, "size": size}
            if quality != "standard":
                gen_kwargs["quality"] = quality
            try:
                resp = client.images.generate(**gen_kwargs)
            except Exception as e:
                st.info(f"Could not generate the image: {e}")
                resp = None

        if not resp or not getattr(resp, "data", None):
            st.info("No image returned. Try a different theme or simplify extras.")
        else:
            with gallery.container():
                for i, item in enumerate(resp.data, start=1):
                    if getattr(item, "b64_json", None):
                        img = Imagine.b64_to_image(item.b64_json)
                        st.image(
                            img, caption=f"{theme_key} — Output {i}", width="stretch"
                        )
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        st.download_button(
                            label=f"Download Image",
                            data=buf.getvalue(),
                            file_name=f"napkin_{i}.png",
                            mime="image/png",
                            width="stretch",
                        )
                    elif getattr(item, "url", None):
                        st.image(
                            item.url,
                            caption=f"{theme_key} — Output {i}",
                            width="stretch",
                        )
                        if hasattr(st, "link_button"):
                            st.link_button(
                                "See in new tab ↗", item.url, width="stretch"
                            )
                        else:
                            st.markdown(
                                f'<a href="{item.url}" target="_blank" rel="noopener noreferrer">See in new tab ↗</a>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.info(f"Result {i}: Unrecognized response format.")
