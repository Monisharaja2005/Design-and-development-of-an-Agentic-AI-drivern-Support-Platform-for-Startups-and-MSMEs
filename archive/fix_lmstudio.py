"""
Run this from D:\\demo\\final:
    python fix_lmstudio.py
"""
import re

f = open('mainp.py', encoding='utf-8')
content = f.read()
f.close()

# Find and replace the _run_vision_ai function
pattern = re.compile(
    r'async def _run_vision_ai\(image_b64: str, mime: str, prompt: str\) -> str:.*?raise Exception\(f"All AI providers failed: \{last_err\}"\)',
    re.DOTALL
)

new_func = '''async def _run_vision_ai(image_b64: str, mime: str, prompt: str) -> str:
    """LM Studio only — no external API calls."""
    result = await _try_lmstudio_vision(image_b64, mime, prompt)
    logger.info("Document validated via LM Studio")
    return result'''

if pattern.search(content):
    content = pattern.sub(new_func, content)
    open('mainp.py', 'w', encoding='utf-8').write(content)
    print("FIXED — LM Studio is now the only provider")
else:
    print("Pattern not found — checking what is there:")
    idx = content.find('async def _run_vision_ai')
    print(content[idx:idx+400])
