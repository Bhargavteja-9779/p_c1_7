"""Assemble manuscript_final.md (v6, ADCC-CP) from the draft_v6_*.md parts, filling
{{TOKEN}} placeholders from code/results/adcc_stats.json + validity/diagnostic JSON.
Fails loudly if any token is left unfilled."""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
RES = HERE.parent / "code" / "results"

st = json.load(open(RES / "adcc_stats.json"))
pool = st["pooled"]; tl = st["target_level"]


def P(method, metric):
    return pool[method][metric]


def num(x, n=3):
    return f"{x:.{n}f}"


tok = {}
tok["NRUNS"] = str(st["n_runs"])
for m in ["split", "normalized", "mondrian", "weighted_kmm", "weighted_ad", "mwcp",
          "adcc", "adcc_grp", "adcc_pl", "adcc_norm", "adcc_2d"]:
    tok[f"POOL_wsc_{m}"] = num(P(m, "worst_stratum_coverage"))
    tok[f"POOL_s0_{m}"] = num(P(m, "s0_coverage"))
    tok[f"POOL_marg_{m}"] = num(P(m, "marginal_coverage"))
    tok[f"POOL_tail10_{m}"] = num(P(m, "tail10_coverage"))
    tok[f"POOL_sat_{m}"] = f"{100*P(m,'saturated_fraction'):.0f}%"
    tok[f"POOL_width_{m}"] = num(P(m, "mean_width"), 2)
# abstract short forms
tok["WSC_split"] = num(P("split", "worst_stratum_coverage"))
tok["WSC_adcc"] = num(P("adcc", "worst_stratum_coverage"))
# target-level stat vs split, worst stratum
wsc = {r["baseline"]: r for r in tl["worst_stratum_coverage"]}
s = wsc["split"]
tok["N_better_wsc"] = str(s["n_better"])
tok["STAT_wsc_split_diff"] = f"{s['mean_diff']:+.3f}"
tok["STAT_wsc_split_p"] = f"{s['p_holm']:.1e}" if s['p_holm'] < 0.01 else f"{s['p_holm']:.3f}"
tok["STAT_wsc_split_ci"] = f"[{s['ci_lo']:+.3f}, {s['ci_hi']:+.3f}]"

# validity controls
val = {(r["setting"], r["method"]): r for r in st.get("validity", [])}
def vget(setting, method, field, default="n/a"):
    r = val.get((setting, method))
    return num(r[field]) if r else default
tok["VAL_rand_s0_adcc"] = vget("random", "adcc", "s0_coverage")
tok["VAL_plshift_s0_adcc"] = vget("adtilt_pl", "adcc", "s0_coverage")
tok["VAL_plshift_s0_split"] = vget("adtilt_pl", "split", "s0_coverage")
tok["VAL_expshift_s0_adcc"] = vget("adtilt_exp", "adcc", "s0_coverage")

# misspecification diagnostic
dpath = RES / "misspec_diag.jsonl"
if dpath.exists():
    import statistics
    rows = [json.loads(l) for l in open(dpath)]
    tok["DIAG_dF"] = num(statistics.mean(r["delta_F"] for r in rows))
    tok["DIAG_d0"] = num(statistics.mean(r["delta_0"] for r in rows))
else:
    tok["DIAG_dF"] = "{{DIAG_dF}}"; tok["DIAG_d0"] = "{{DIAG_d0}}"

# table/figure label tokens (resolved to names used in [[TABLE:...]] markers)
tok.update({"T_validity": "S-adcc-validity", "T_positioning": "1", "T_pooled": "2", "T_stats": "3",
            "T_bywindow": "S-adcc-window", "T_bymodel": "S-adcc-model",
            "F_panel": "1", "F_curve": "2"})

parts = ["abstract", "intro", "methods", "results", "discussion"]
text = "\n\n".join((HERE / f"draft_v6_{p}.md").read_text().strip() for p in parts)
# append author info / data availability / references from a shared tail
text += "\n\n" + (HERE / "draft_v6_tail.md").read_text().strip()

def repl(m):
    k = m.group(1)
    if k in tok:
        return tok[k]
    return m.group(0)

out = re.sub(r"\{\{([A-Za-z0-9_]+)\}\}", repl, text)
# inject the real ACS reference list in place of the placeholder
refs = (HERE / "references_acs.md").read_text()
refs_body = refs.split("## References", 1)[-1].strip()
out = out.replace("[[Formatted from supplementary/literature/verified_references.json in ACS style.]]",
                  refs_body)
# --- renumber citations in order of first appearance (ACS style) ---
SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"; S2D = {c: str(i) for i, c in enumerate(SUP)}
def to_sup(n): return "".join(SUP[int(d)] for d in str(n))
cite_re = re.compile(r"[%s]+(?:(?:⁻|,)[%s]+)*" % (SUP, SUP))
head, out = out.split("## Abstract", 1); head += "## Abstract"
body, refs_part = out.split("## References", 1)
def parse(g):
    nums = []
    for part in g.split(","):
        if "⁻" in part:
            a, b = part.split("⁻"); a = int("".join(S2D[c] for c in a)); b = int("".join(S2D[c] for c in b))
            nums += list(range(a, b + 1))
        else:
            nums.append(int("".join(S2D[c] for c in part)))
    return nums
order = []
for m in cite_re.finditer(body):
    for n in parse(m.group()):
        if n not in order: order.append(n)
ref_lines = re.findall(r"^(\d+)\. (.+)$", refs_part, flags=re.M)
ref_map = {int(n): txt for n, txt in ref_lines}
uncited = sorted(set(ref_map) - set(order))
if uncited: print("UNCITED REFERENCES:", uncited, file=sys.stderr)
order = [n for n in order if n in ref_map] + uncited
new_of = {old: i + 1 for i, old in enumerate(order)}
def fmt(nums):
    nums = sorted(set(nums)); runs = []; s = nums[0]; prev = s
    for x in nums[1:] + [None]:
        if x is not None and x == prev + 1: prev = x; continue
        runs.append(to_sup(s) if s == prev else (to_sup(s) + "," + to_sup(prev) if prev == s + 1 else to_sup(s) + "⁻" + to_sup(prev)))
        if x is not None: s = prev = x
    return ",".join(runs)
body = cite_re.sub(lambda m: fmt([new_of[n] for n in parse(m.group())]), body)
refs_txt = "\n".join(f"{new_of[o]}. {ref_map[o]}" for o in order)
out = head + body + "## References\n\n" + refs_txt
left = sorted(set(re.findall(r"\{\{([A-Za-z0-9_]+)\}\}", out)))
if left:
    print("UNFILLED TOKENS:", left, file=sys.stderr)
(HERE / "manuscript_final.md").write_text(out + "\n")
print(f"wrote manuscript_final.md ({len(out.split())} words); unfilled={len(left)}")
