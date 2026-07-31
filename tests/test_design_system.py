import re
from pathlib import Path

STYLE_PATH = Path(__file__).parent.parent / "app" / "static" / "style.css"

MIN_TOKENS = {
    "--color-bg",
    "--color-surface",
    "--color-ink",
    "--color-muted",
    "--color-accent",
    "--color-accent-ink",
    "--color-positive",
    "--color-negative",
    "--color-border",
    "--space-1",
    "--space-2",
    "--space-3",
    "--space-4",
    "--radius",
}

COLOR_TOKENS = {
    "ink": "--color-ink",
    "muted": "--color-muted",
    "accent": "--color-accent",
    "positive": "--color-positive",
    "negative": "--color-negative",
}
BACKGROUND_TOKENS = {"surface": "--color-surface", "bg": "--color-bg"}


def lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(hex_a, hex_b):
    la, lb = relative_luminance(hex_a), relative_luminance(hex_b)
    la, lb = max(la, lb), min(la, lb)
    return (la + 0.05) / (lb + 0.05)


def stylesheet_text():
    return STYLE_PATH.read_text()


def root_block(css):
    match = re.search(r":root\s*\{([^}]*)\}", css)
    assert match, "no :root block found"
    return match.group(1)


def dark_block(css):
    match = re.search(
        r"@media\s*\(prefers-color-scheme:\s*dark\)\s*\{\s*:root\s*\{([^}]*)\}",
        css,
    )
    assert match, "no dark-mode :root override found"
    return match.group(1)


def parse_tokens(block):
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", block))


def test_root_declares_minimum_token_set():
    tokens = parse_tokens(root_block(stylesheet_text()))
    missing = MIN_TOKENS - tokens.keys()
    assert not missing, f"missing tokens in :root: {missing}"


def test_dark_mode_overrides_every_color_token():
    css = stylesheet_text()
    light = parse_tokens(root_block(css))
    dark = parse_tokens(dark_block(css))
    light_colors = {k for k in light if k.startswith("--color-")}
    missing = light_colors - dark.keys()
    assert not missing, f"dark mode does not override: {missing}"


def _theme_tokens(css, dark: bool):
    tokens = parse_tokens(root_block(css))
    if dark:
        tokens.update(parse_tokens(dark_block(css)))
    return tokens


def test_all_token_pairs_meet_aa_contrast():
    css = stylesheet_text()
    failures = []
    for theme, is_dark in [("light", False), ("dark", True)]:
        tokens = _theme_tokens(css, is_dark)
        for text_name, text_var in COLOR_TOKENS.items():
            for bg_name, bg_var in BACKGROUND_TOKENS.items():
                ratio = contrast_ratio(tokens[text_var], tokens[bg_var])
                if ratio < 4.5:
                    failures.append(
                        f"{theme}: {text_name} on {bg_name} = {ratio:.2f}"
                    )
    assert not failures, "contrast failures:\n" + "\n".join(failures)


def test_focus_visible_defined_for_interactive_elements():
    css = stylesheet_text()
    assert ":focus-visible" in css
    rule = re.search(r"([^{}]*:focus-visible[^{]*)\{", css).group(1)
    for tag in ["button", "input", "select"]:
        assert tag in rule, f"{tag} missing from :focus-visible rule"


def _assert_no_inline_styles(html: str, where: str):
    assert 'style="' not in html, f"inline style found in {where}"


def test_group_pages_have_no_inline_styles(client, group_with_members):
    group_id = group_with_members(["Ana", "Ben"])
    _assert_no_inline_styles(client.get("/groups").text, "group list")
    _assert_no_inline_styles(client.get(f"/groups/{group_id}").text, "group detail")


def test_expense_form_partial_has_no_inline_styles(
    client, group_with_members, member_ids
):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = client.post(
        f"/groups/{group_id}/expenses",
        data={
            "description": "Lunch",
            "amount": "10.00",
            "payer_id": str(ana),
            "participants": [str(ana), str(ben)],
        },
    )
    _assert_no_inline_styles(resp.text, "expense partial")


def test_color_scheme_meta_present(client):
    html = client.get("/groups").text
    assert '<meta name="color-scheme" content="light dark">' in html
