src = open(__import__("os").path.join(__import__("os").path.dirname(__file__), "generate_figures.py")).read()
exec(src[:src.index("EX = {")])
import cairosvg

_place = place
def svg2(p, hipx=200, front=False, lift=0):
    global place
    def pl(J, hx):
        P = _place(J, hx)
        return {k: (v[0], v[1] - lift) for k, v in P.items()}
    place = pl
    try:
        return svg(p, hipx=hipx, front=front)
    finally:
        place = _place

cuad = dict(torso=110, headA=100, uaN=0, faN=0, uaF=0, faF=0, thN=0, shN=-90, ftN=-100, thF=0, shF=-90, ftF=-100)
NEW = {
 "salto": (pose(torso=145, headA=160, thN=85, shN=-20, thF=85, shF=-20, uaN=-40, faN=-25, uaF=-50, faF=-35),
           pose(uaN=150, faN=158, uaF=142, faF=150, ftN=25, ftF=20, thF=-6, shF=-10), {"lift2": 22}),
 "patada": (pose(**cuad), pose(**dict(cuad, thN=-100, shN=175, ftN=-90)), {"hipx": 160}),
 "piernas": (pose(torso=-90, headA=-90, uaN=90, faN=90, uaF=90, faF=90, thN=90, shN=90, ftN=180, thF=90, shF=90, ftF=180),
             pose(torso=-90, headA=-90, uaN=90, faN=90, uaF=90, faF=90, thN=180, shN=180, ftN=90, thF=178, shF=178, ftF=90), {"hipx": 200}),
 "pica": (pose(torso=40, headA=30, uaN=45, faN=45, uaF=45, faF=45, thN=-35, shN=-35, ftN=0, thF=-35, shF=-35, ftF=0),
          pose(torso=55, headA=20, uaN=-10, faN=45, uaF=-10, faF=45, thN=-35, shN=-35, ftN=0, thF=-35, shF=-35, ftF=0), {"hipx": 190}),
 "bisagra": (pose(),
             pose(torso=100, headA=100, uaN=2, faN=4, uaF=-4, faF=-2, thN=8, shN=-8, thF=8, shF=-8), {"hipx": 170}),
}
from PIL import Image
sheet = Image.new("RGB", (800, 300*len(NEW)), "white")
for i, (name, (a, b, opt)) in enumerate(NEW.items()):
    for j, (tag, p) in enumerate((("inicio", a), ("fin", b))):
        lift = opt.get("lift2", 0) if tag == "fin" else 0
        s = svg2(p, hipx=opt.get("hipx", 200), lift=lift)
        if name == "salto":
            s = s.replace('viewBox="0 0 400 300"', 'viewBox="-40 -60 480 360"').replace('<rect width="400" height="300"', '<rect x="-40" y="-60" width="480" height="360"').replace('x1="20"', 'x1="-20"').replace('x2="380"', 'x2="420"')
        open(f"svg/{name}-{tag}.svg", "w").write(s)
        cairosvg.svg2png(bytestring=s.encode(), write_to=f"svg/{name}-{tag}.png")
        sheet.paste(Image.open(f"svg/{name}-{tag}.png").convert("RGB"), (j*400, i*300))
sheet.resize((400, 150*len(NEW))).save("sheet2.png")
print("ok")
