"""Break down where the tokens go in White's latest request dump. Usage: python context_size.py <hermes root>"""
import glob
import json
import os
import sys

root = sys.argv[1]
dumps = sorted(glob.glob(os.path.join(root, "**", "request_dump_*.json"), recursive=True), key=os.path.getmtime)
d = json.load(open(dumps[-1], encoding="utf-8"))
body = d["request"]["body"]
tok = lambda s: len(s) // 4  # noqa: E731  rough: 4 chars per token
msgs = body.get("messages", [])
tools = body.get("tools", [])
sys_txt = "".join(m["content"] if isinstance(m.get("content"), str) else json.dumps(m.get("content"))
                  for m in msgs if m.get("role") == "system")
print("dump:", os.path.basename(dumps[-1]))
print("system prompt ~tokens:", tok(sys_txt))
print("tools:", len(tools), "~tokens:", tok(json.dumps(tools)))
print("other messages ~tokens:", tok(json.dumps([m for m in msgs if m.get("role") != "system"])))
names = sorted(((tok(json.dumps(t)), t.get("function", {}).get("name")) for t in tools), reverse=True)
print("biggest tools:", names[:12])
groups = {}
for _, n in names:
    k = n.split("_")[0] if n.startswith("mcp") is False else "_".join(n.split("__")[:2])
    groups[k] = groups.get(k, 0) + 1
print("tool groups:", sorted(groups.items(), key=lambda x: -x[1])[:15])
# Sections of the system prompt by markdown headings
import re
parts = re.split(r"\n(?=#{1,3} )", sys_txt)
sizes = sorted(((tok(p), p.strip().splitlines()[0][:70]) for p in parts if p.strip()), reverse=True)
print("biggest system sections:", sizes[:12])
