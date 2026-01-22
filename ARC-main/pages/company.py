import streamlit as st
from crowdlike.ui import apply_ui, soft_divider
from crowdlike.site import site_footer, site_header, site_hero, site_section
from crowdlike.version import VERSION

st.set_page_config(page_title="Crowdlike — Company", page_icon="🏢", layout="wide")
apply_ui()

site_header(active="company")


site_hero(kicker=f"Crowdlike v{VERSION}", title="Company", subtitle="What Crowdlike is building and why: safe agentic commerce with human-aligned controls.")

soft_divider()

site_section(icon="🎯", title="Mission", body="Make agent autonomy feel safe, legible, and user-controlled—without losing speed or fun.", full_width=True)
site_section(icon="🧩", title="Design principles", body="Clear next steps, guardrails first, explanations always, minimal clutter.", full_width=True)

site_footer()
