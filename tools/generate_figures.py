import math, os, cairosvg

W, H, GROUND = 400, 300, 256
NEAR, FAR, BG, LINE = "#15302E", "#8FA8A3", "#F4F8F6", "#C9D8D3"
L = dict(torso=80, neck=24, head=19, uarm=45, farm=42, thigh=60, shin=58, foot=15)

def vec(a, l):
    r = math.radians(a)
    return (math.sin(r) * l, math.cos(r) * l)

def add(p, v):
    return (p[0] + v[0], p[1] + v[1])

def build(p):
    hip = (0, 0)
    neck = add(hip, vec(p["torso"], L["torso"]))
    head = add(neck, vec(p.get("headA", p["torso"]), L["neck"]))
    J = dict(hip=hip, neck=neck, head=head)
    for s in ("N", "F"):
        sh = add(neck, vec(p["torso"] + 180, 12))
        J["shoulder"] = sh
        e = add(sh, vec(p["ua" + s], L["uarm"]))
        h = add(e, vec(p["fa" + s], L["farm"]))
        k = add(hip, vec(p["th" + s], L["thigh"]))
        a = add(k, vec(p["sh" + s], L["shin"]))
        t = add(a, vec(p.get("ft" + s, 90), L["foot"]))
        J.update({"elbow" + s: e, "hand" + s: h, "knee" + s: k, "ankle" + s: a, "toe" + s: t})
    return J

def place(J, hipx):
    ys = [v[1] for k, v in J.items() if k != "head"] + [J["head"][1] + L["head"]]
    dy = GROUND - 5 - max(ys)
    dx = hipx - J["hip"][0]
    return {k: (v[0] + dx, v[1] + dy) for k, v in J.items()}

def line(pts, color, w=11):
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'

def svg(p, hipx=200, front=False):
    J = place(build(p), hipx)
    far = NEAR if front else FAR
    parts = [f'<rect width="{W}" height="{H}" fill="{BG}"/>',
             f'<line x1="20" y1="{GROUND}" x2="{W-20}" y2="{GROUND}" stroke="{LINE}" stroke-width="4" stroke-linecap="round"/>']
    parts.append(line([J["hip"], J["kneeF"], J["ankleF"], J["toeF"]], far))
    parts.append(line([J["shoulder"], J["elbowF"], J["handF"]], far))
    parts.append(line([J["hip"], J["neck"]], NEAR, 13))
    parts.append(line([J["hip"], J["kneeN"], J["ankleN"], J["toeN"]], NEAR))
    parts.append(line([J["shoulder"], J["elbowN"], J["handN"]], NEAR))
    hx, hy = J["head"]
    parts.append(f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="{L["head"]}" fill="{NEAR}"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">' + "".join(parts) + "</svg>"

def pose(**kw):
    base = dict(torso=180, uaN=14, faN=10, uaF=-14, faF=-10, thN=0, shN=0, thF=0, shF=0)
    base.update(kw)
    return base

def plank(phi, **kw):
    legs = -(90 - phi)
    return pose(torso=180 + legs, headA=180 + legs - 10, thN=legs, shN=legs, thF=legs, shF=legs, ftN=0, ftF=0, **kw)

phi_top = math.degrees(math.asin(77 / 186))
phi_low = math.degrees(math.asin(32 / 186))
lying = dict(torso=-90, headA=-90, uaN=90, faN=90, uaF=90, faF=90, thN=135, shN=24, thF=135, shF=24)

EX = {
 "sentadilla": (pose(), pose(torso=145, headA=160, thN=85, shN=-20, thF=85, shF=-20, uaN=90, faN=90, uaF=90, faF=90), {}),
 "flexion": (plank(phi_top, uaN=0, faN=0, uaF=0, faF=0), plank(phi_low, uaN=-90, faN=0, uaF=-90, faF=0), {"hipx": 170}),
 "zancada": (pose(), pose(thN=90, shN=0, thF=-25, shF=-86, ftF=-10), {}),
 "puente": (pose(**lying), pose(torso=-68, headA=-90, uaN=95, faN=90, uaF=95, faF=90, thN=112, shN=18, thF=112, shF=18), {"hipx": 190}),
 "crunch": (pose(**lying), pose(torso=-125, headA=-115, uaN=100, faN=100, uaF=100, faF=100, thN=135, shN=24, thF=135, shF=24), {"hipx": 200}),
 "jumping": (pose(uaN=12, faN=10, uaF=-12, faF=-10, thN=5, shN=5, thF=-5, shF=-5, ftN=90, ftF=-90),
             pose(uaN=150, faN=165, uaF=-150, faF=-165, thN=24, shN=24, thF=-24, shF=-24, ftN=90, ftF=-90), {"front": True}),
 "escaladores": (plank(phi_top, uaN=0, faN=0, uaF=0, faF=0), dict(plank(phi_top, uaN=0, faN=0, uaF=0, faF=0), thN=30, shN=-60, ftN=10), {"hipx": 170}),
 "talones": (pose(), pose(ftN=25, ftF=25), {}),
 "superman": (pose(torso=90, headA=90, uaN=90, faN=90, uaF=90, faF=90, thN=-90, shN=-90, thF=-90, shF=-90, ftN=-180, ftF=-180),
              pose(torso=100, headA=105, uaN=108, faN=110, uaF=108, faF=110, thN=-98, shN=-100, thF=-98, shF=-100, ftN=-180, ftF=-180), {"hipx": 190}),
 "rodillas": (pose(), pose(thN=90, shN=0, ftN=60, uaN=-35, faN=-10, uaF=40, faF=120), {}),
}

os.makedirs("svg", exist_ok=True)
for name, (a, b, opt) in EX.items():
    for tag, p in (("inicio", a), ("fin", b)):
        s = svg(p, hipx=opt.get("hipx", 200), front=opt.get("front", False))
        open(f"svg/{name}-{tag}.svg", "w").write(s)
        cairosvg.svg2png(bytestring=s.encode(), write_to=f"svg/{name}-{tag}.png")
print("ok")
