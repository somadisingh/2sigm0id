"""Make your local MiroFish produce English personas.

    python patch_mirofish_english.py ../../MiroFish        (path to your MiroFish folder)

Run it once, then restart MiroFish (Ctrl+C, then npm run dev). It changes only your local copy,
never the team repo. It's safe to run twice. To undo it: cd MiroFish && git checkout .

What it changes:
  1. Default language zh -> en, so any step that runs without the page's language setting
     still gets English (backend and the web page).
  2. The persona prompt: asks for the country in English instead of Chinese, and adds a firm
     instruction that EVERY field (bio, persona, profession, topics) is in English.
"""
import sys
from pathlib import Path

ENGLISH_RULE = ("IMPORTANT: Write every field (bio, persona, profession, country, interested_topics) "
                "in English only. Do not use any Chinese characters.")

EDITS = [
    ("backend/app/utils/locale.py",
     [("request.headers.get('Accept-Language', 'zh')", "request.headers.get('Accept-Language', 'en')"),
      ("return raw if raw in _translations else 'zh'", "return raw if raw in _translations else 'en'"),
      ("return getattr(_thread_local, 'locale', 'zh')", "return getattr(_thread_local, 'locale', 'en')"),
      ("lang_config = _languages.get(locale, _languages.get('zh', {}))",
       "lang_config = _languages.get(locale, _languages.get('en', {}))")]),
    ("frontend/src/i18n/index.js",
     [("localStorage.getItem('locale') || 'zh'", "localStorage.getItem('locale') || 'en'")]),
    ("backend/app/services/oasis_profile_generator.py",
     [('6. country: 国家（使用中文，如"中国"）', '6. country: country, in English (e.g. "United States")'),
      ("- {get_language_instruction()} (gender字段必须用英文male/female)",
       "- {get_language_instruction()} (gender字段必须用英文male/female)\n- " + ENGLISH_RULE),
      ('- {get_language_instruction()} (gender字段必须用英文"other")',
       '- {get_language_instruction()} (gender字段必须用英文"other")\n- ' + ENGLISH_RULE)]),
]


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python patch_mirofish_english.py PATH/TO/MiroFish")
    root = Path(sys.argv[1]).expanduser().resolve()
    if not (root / "backend" / "app").is_dir():
        sys.exit(f"{root} doesn't look like the MiroFish folder (no backend/app inside).")

    problems = 0
    for rel, pairs in EDITS:
        path = root / rel
        text = path.read_text(encoding="utf-8")
        for old, new in pairs:
            if new in text:
                status = "already done"
            elif text.count(old) >= 1:
                text = text.replace(old, new)
                status = "changed"
            else:
                status = "NOT FOUND (MiroFish may have changed; tell Claude)"
                problems += 1
            print(f"{rel}: {status}: {old[:60]}")
        path.write_text(text, encoding="utf-8")

    print("\nDone." if not problems else f"\nDone with {problems} edit(s) not applied.")
    print("Restart MiroFish (Ctrl+C, then npm run dev) and reload the page before the next batch.")


if __name__ == "__main__":
    main()
