"""
Patch script: adds html.escape() XSS protection to ui_components.py
Run once from project root: python patch_ui.py
"""
import re

with open('ui_components.py', 'r', encoding='utf-8') as f:
    src = f.read()

# ── 1. Add `import html` before `import streamlit as st` ─────────────────────
if 'import html\n' not in src:
    src = src.replace('\nimport streamlit as st\n', '\nimport html\nimport streamlit as st\n', 1)

# ── 2. render_alert_card — escape title, message, action ─────────────────────
old_alert = (
    "    title = str(alert.get(\"title\", \"Alert\"))\n"
    "    message = str(alert.get(\"message\", \"\"))\n"
)
new_alert = (
    "    title = html.escape(str(alert.get(\"title\", \"Alert\")))\n"
    "    message = html.escape(str(alert.get(\"message\", \"\")))\n"
)
src = src.replace(old_alert, new_alert, 1)

old_action = (
    "    action = str(alert.get(\"action\", \"\")).strip()\n"
    "    action_html = (\n"
    "        f'<div style=\"font-size:0.78rem;color:{C[\"info\"]};'\n"
    "        f'border-top:1px solid {C[\"border\"]};'\n"
    "        f'padding-top:8px;margin-top:10px;line-height:1.4;\">'\n"
    "        f'<strong>Action required:</strong> {action}</div>'\n"
    "    ) if action else \"\"\n"
)
new_action = (
    "    action = html.escape(str(alert.get(\"action\", \"\")).strip())\n"
    "    action_html = (\n"
    "        f'<div style=\"font-size:0.78rem;color:{C[\"info\"]};'\n"
    "        f'border-top:1px solid {C[\"border\"]};'\n"
    "        f'padding-top:8px;margin-top:10px;line-height:1.4;\">'\n"
    "        f'<strong>Action required:</strong> {action}</div>'\n"
    "    ) if action else \"\"\n"
)
src = src.replace(old_action, new_action, 1)

# ── 3. render_insight_card — escape user-data fields ─────────────────────────
old_ins_fields = (
    "    cat = str(insight.get(\"category\", \"\"))\n"
    "    cat_display = CAT_LABEL.get(cat, cat.replace(\"_\", \" \").title())\n"
)
new_ins_fields = (
    "    cat = str(insight.get(\"category\", \"\"))\n"
    "    cat_display = html.escape(CAT_LABEL.get(cat, cat.replace(\"_\", \" \").title()))\n"
)
src = src.replace(old_ins_fields, new_ins_fields, 1)

# Replace the 4 insight.get() calls inside the HTML f-string
src = src.replace(
    "{insight.get('title', '')}",
    "{html.escape(str(insight.get('title', '')))}",
    1
)
src = src.replace(
    "{insight.get('metric', '')}",
    "{html.escape(str(insight.get('metric', '')))}",
    1
)
src = src.replace(
    "{insight.get('forecast', '')}",
    "{html.escape(str(insight.get('forecast', '')))}",
    1
)
src = src.replace(
    "{insight.get('recommendation', '')}",
    "{html.escape(str(insight.get('recommendation', '')))}",
    1
)

# ── 4. render_recommendation_item — escape text ──────────────────────────────
src = src.replace(
    "    <strong style=\"color:{C['navy']};\">{index}.</strong>&nbsp;{text}\n",
    "    <strong style=\"color:{C['navy']};\">{index}.</strong>&nbsp;{html.escape(str(text))}\n",
    1
)

import tempfile, shutil, os
tmp = 'ui_components_patched.py'
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(src)
shutil.move(tmp, 'ui_components.py')

# ── Verify ────────────────────────────────────────────────────────────────────
with open('ui_components.py', 'r', encoding='utf-8') as f:
    result = f.read()

checks = [
    'import html',
    'html.escape(str(alert.get("title"',
    'html.escape(str(alert.get("message"',
    'html.escape(str(alert.get("action"',
    "html.escape(CAT_LABEL.get(",
    "html.escape(str(insight.get('title'",
    "html.escape(str(insight.get('metric'",
    "html.escape(str(insight.get('forecast'",
    "html.escape(str(insight.get('recommendation'",
    "html.escape(str(text))",
]

with open('patch_result.txt', 'w', encoding='utf-8') as out:
    for check in checks:
        found = check in result
        out.write(f"{'OK' if found else 'MISSING'}: {check}\n")
    out.write("DONE\n")
