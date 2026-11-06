# -*- coding: utf-8 -*-
"""뇌 탭 그림·자료 만들기 (한 번만 돌리면 됨, 토큰 0).

    python robot/brain_build.py --text                    # data/brain/regions.json 만 (표를 고쳤을 때)
    python robot/brain_build.py --atlas /경로/neuroparc    # 평면 그림 6면 + 3D 모형까지

그림 재료 (모두 MNI152 표준 뇌 1mm, neuroparc 저장소 github.com/neurodata/neuroparc 에서):
  AAL (116 부위) · Harvard-Oxford 피질하 · JHU 백질 길. 배경 MRI 는 nilearn 에 들어 있는 MNI152 2009 T1.
  아틀라스에 없는 작은 핵(시상하부·흑질·복측피개영역·청반·솔기핵·뇌하수체·송과선)은 논문에 나오는 MNI 좌표에
  작은 타원을 놓아 '대략 자리'로 그렸다. 뇌간 셋(중뇌·뇌교·연수)은 높이(z)로 나눈 대략 경계.

만드는 것 (data/brain/)
  regions.json  부위 52개 (robot/brain_regions.py 그대로 + 그림 조각 목록)
  atlas.json    평면 그림 6면: 면마다 배경 그림, 조각(atom)별 SVG 경로
  img/<면>.webp 배경 (옆·안쪽·아래 = 입체 음영, 단면 = MRI)
  mesh.bin      3D 조각별 삼각형 (int16 좌표 0.1mm, uint16 번호)  ·  mesh.json 조각 목록
"""
import argparse, json, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brain_regions as BR

OUT = os.path.join(HERE, "..", "data", "brain")

# ───── 조각(atom) — 서로 겹치지 않는 가장 작은 칸. 부위 = 조각들의 묶음 ─────
# 이름: (설명, AAL 번호들)  — AAL1 표준 순서, 홀수 = 왼쪽, 짝수 = 오른쪽
AAL_ATOMS = {
    "motor": [1, 2], "dlpfc": [3, 4, 7, 8], "ofc": [5, 6, 9, 10, 15, 16], "broca": [11, 12, 13, 14],
    "frontal_x": [17, 18, 21, 22, 69, 70], "sma": [19, 20], "mpfc": [23, 24], "vmpfc": [25, 26], "rectus": [27, 28],
    "insula": [29, 30], "acc": [31, 32], "mcc": [33, 34], "pcc": [35, 36],
    "hippocampus": [37, 38], "parahipp": [39, 40], "amygdala": [41, 42],
    "v1": [43, 44], "occ_x": list(range(45, 55)), "fusiform": [55, 56],
    "somato": [57, 58], "spl": [59, 60], "ipl_x": [61, 62, 63, 64], "angular": [65, 66], "precuneus": [67, 68],
    "caudate": [71, 72], "putamen": [73, 74], "pallidus": [75, 76], "thalamus": [77, 78],
    "auditory": [79, 80], "stg": [81, 82], "tpole": [83, 84, 87, 88], "temp_x": [85, 86, 89, 90],
    "cerebellum": list(range(91, 117)),
}
DEEP = ["midbrain", "pons", "medulla", "accumbens", "ventricle", "whitematter", "cc", "fornix",
        "hypothalamus", "sn", "vta", "lc", "raphe", "pituitary", "pineal", "wernicke"]
# 작은 핵 — (가운데 MNI x,y,z, 반지름 mm). 좌우 한 쌍이면 x 를 ± 로.
BLOBS = {
    "hypothalamus": [((-4, -5, -10), (4, 6, 5)), ((4, -5, -10), (4, 6, 5))],
    "sn": [((-11, -18, -12), (3, 7, 3)), ((11, -18, -12), (3, 7, 3))],
    "vta": [((-4, -16, -14), (3, 3, 3)), ((4, -16, -14), (3, 3, 3))],
    "lc": [((-5, -37, -26), (2.5, 2.5, 5)), ((5, -37, -26), (2.5, 2.5, 5))],
    "raphe": [((0, -30, -24), (2, 4, 14))],
    "pituitary": [((0, 0, -36), (6, 5, 4))],
    "pineal": [((0, -31, 2), (3, 4, 3))],
}
LOBE_OF = {}   # 조각 → 큰 갈래 색
for a in ["motor", "dlpfc", "ofc", "broca", "frontal_x", "sma", "mpfc", "vmpfc", "rectus"]: LOBE_OF[a] = "frontal"
for a in ["somato", "spl", "ipl_x", "angular", "precuneus"]: LOBE_OF[a] = "parietal"
for a in ["auditory", "stg", "wernicke", "tpole", "temp_x", "fusiform"]: LOBE_OF[a] = "temporal"
for a in ["v1", "occ_x"]: LOBE_OF[a] = "occipital"
for a in ["insula"]: LOBE_OF[a] = "insula"
for a in ["acc", "mcc", "pcc", "hippocampus", "parahipp", "amygdala", "fornix"]: LOBE_OF[a] = "limbic"
for a in ["caudate", "putamen", "pallidus", "accumbens"]: LOBE_OF[a] = "basal"
for a in ["thalamus", "hypothalamus", "pineal", "pituitary"]: LOBE_OF[a] = "dien"
for a in ["midbrain", "pons", "medulla", "sn", "vta", "lc", "raphe"]: LOBE_OF[a] = "stem"
LOBE_OF.update(cerebellum="cerebellum", ventricle="csf", whitematter="wm", cc="wm")

# 부위 → 조각 (L = 왼쪽만)
FRONTAL = ["motor", "dlpfc", "ofc", "broca", "frontal_x", "sma", "mpfc", "vmpfc", "rectus"]
PARIETAL = ["somato", "spl", "ipl_x", "angular", "precuneus"]
TEMPORAL = ["auditory", "stg", "wernicke", "tpole", "temp_x"]
OCCIPITAL = ["v1", "occ_x"]
CORTEX = FRONTAL + PARIETAL + TEMPORAL + OCCIPITAL + ["fusiform", "insula", "acc", "mcc", "pcc", "parahipp"]
REGION_ATOMS = {
    "frontal": FRONTAL, "parietal": PARIETAL, "temporal": TEMPORAL + ["fusiform"], "occipital": OCCIPITAL,
    "hippocampus": ["hippocampus"], "amygdala": ["amygdala"], "thalamus": ["thalamus"], "hypothalamus": ["hypothalamus"],
    "cerebellum": ["cerebellum"], "midbrain": ["midbrain", "sn", "vta"], "pons": ["pons", "lc"], "medulla": ["medulla"],
    "cortex": CORTEX, "limbic": ["acc", "mcc", "pcc", "hippocampus", "parahipp", "amygdala", "fornix", "hypothalamus"],
    "basal": ["caudate", "putamen", "pallidus", "accumbens", "sn"], "brainstem": ["midbrain", "pons", "medulla", "sn", "vta", "lc", "raphe"],
    "diencephalon": ["thalamus", "hypothalamus", "pineal"],
    "prefrontal": ["dlpfc", "ofc", "broca", "mpfc", "vmpfc", "rectus"], "dlpfc": ["dlpfc"], "vmpfc": ["vmpfc", "rectus"],
    "ofc": ["ofc", "rectus"], "motor": ["motor"], "sma": ["sma"], "broca": ["broca:L"],
    "somato": ["somato"], "spl": ["spl"], "ipl": ["ipl_x", "angular"], "angular": ["angular"], "precuneus": ["precuneus"],
    "auditory": ["auditory"], "wernicke": ["wernicke:L"], "fusiform": ["fusiform"], "parahipp": ["parahipp"], "temporalpole": ["tpole"],
    "v1": ["v1"], "insula": ["insula"], "acc": ["acc"], "pcc": ["pcc"],
    "caudate": ["caudate"], "putamen": ["putamen"], "pallidus": ["pallidus"], "accumbens": ["accumbens"],
    "sn": ["sn"], "vta": ["vta"], "lc": ["lc"], "raphe": ["raphe"], "pituitary": ["pituitary"], "pineal": ["pineal"],
    "cc": ["cc"], "fornix": ["fornix"], "ventricle": ["ventricle"], "whitematter": ["whitematter", "cc"],
}
APPROX = {"hypothalamus", "sn", "vta", "lc", "raphe", "pituitary", "pineal", "midbrain", "pons", "medulla", "wernicke"}

VIEWS = [  # id, 이름, 종류, 설명
    ("lat", "옆면", "proj", "왼쪽 뇌를 왼쪽 옆에서 본 모습 · 왼쪽이 얼굴 쪽"),
    ("med", "안쪽 면", "proj", "좌우 뇌를 가운데로 갈라 왼쪽 뇌의 안쪽 벽을 본 모습 · 왼쪽이 얼굴 쪽"),
    ("inf", "아래 면", "proj", "뇌를 밑에서 올려다본 모습 (소뇌·뇌간은 떼어 냄) · 위쪽이 얼굴 쪽"),
    ("cor", "앞 단면", "slice", "귀 바로 앞을 세로로 자른 단면 (MRI) · 얼굴 쪽에서 본 모습, 화면 왼쪽 = 오른쪽 뇌"),
    ("cor2", "해마 단면", "slice", "귀 높이에서 세로로 자른 단면 (MRI) · 해마가 잘 보이는 자리"),
    ("ax", "가로 단면", "slice", "눈썹 조금 위 높이를 가로로 자른 단면 (MRI) · 위쪽이 얼굴 쪽"),
]


def text_only():
    os.makedirs(OUT, exist_ok=True)
    regs = []
    for r in BR.R:
        o = {k: r[k] for k in ["id", "ko", "alt", "en", "lv", "up", "origin", "one", "role", "like", "where", "hurt", "pair", "wiki", "kw", "kwen"]}
        o["atoms"] = REGION_ATOMS[r["id"]]
        if r["id"] in APPROX: o["approx"] = 1
        regs.append(o)
    lobes = {"frontal": "전두엽", "parietal": "두정엽", "temporal": "측두엽", "occipital": "후두엽", "insula": "섬엽", "limbic": "변연계",
             "basal": "기저핵", "dien": "간뇌", "stem": "뇌간", "cerebellum": "소뇌", "csf": "뇌실", "wm": "백질"}
    json.dump({"v": 1, "order": BR.ORDER, "regions": regs, "lobeOf": LOBE_OF, "lobes": lobes,
               "views": [{"id": v[0], "name": v[1], "kind": v[2], "note": v[3]} for v in VIEWS],
               "credit": "그림: MNI152 표준 뇌 · AAL(Tzourio-Mazoyer 2002) · Harvard-Oxford(FSL) · JHU 백질 아틀라스 — neuroparc 저장소. 작은 핵은 대략 자리."},
              open(os.path.join(OUT, "regions.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print("regions.json", len(regs))


def build_atlas(root):
    import numpy as np, nibabel as nib
    from scipy import ndimage as ndi
    from skimage import measure
    from PIL import Image
    H = os.path.join(root, "atlases", "label", "Human")
    ld = lambda f: nib.load(os.path.join(H, f))
    aal_i = ld("AAL_space-MNI152NLin6_res-1x1x1.nii.gz"); aff = aal_i.affine
    aal = np.asarray(aal_i.dataobj).astype(np.int16)
    ho = np.asarray(ld("HarvardOxfordsub-maxprob-thr25_space-MNI152NLin6_label_all_res-1x1x1.nii.gz").dataobj).astype(np.int16)
    jhu = np.asarray(ld("JHU_space-MNI152NLin6_res-1x1x1.nii.gz").dataobj).astype(np.int16)
    shp = aal.shape
    ii, jj, kk = np.indices(shp)
    X = aff[0, 0] * ii + aff[0, 3]; Y = aff[1, 1] * jj + aff[1, 3]; Z = aff[2, 2] * kk + aff[2, 3]

    atoms = []; L = np.zeros(shp, np.int16)
    def put(name, mask, only_empty=False):
        nonlocal L
        for side, sm in (("L", X < 0), ("R", X >= 0)) if name not in ("raphe", "pituitary", "pineal") else (("M", np.ones(shp, bool)),):
            m = mask & sm
            if only_empty: m &= (L == 0)
            if not m.any(): continue
            key = name + ":" + side
            if key not in atoms: atoms.append(key)
            L[m] = atoms.index(key) + 1
    # 바닥: 백질·뇌실 (아틀라스 빈 곳만), 그 위에 AAL, 그 위에 깊은 구조
    for n, vals in AAL_ATOMS.items(): put(n, np.isin(aal, vals))
    # 베르니케: 왼쪽 위관자이랑 뒤쪽 (y < -24)
    put("wernicke", np.isin(aal, [81]) & (Y < -24))
    stem = (ho == 8) & (aal == 0)
    put("midbrain", stem & (Z >= -19)); put("pons", stem & (Z < -19) & (Z >= -43)); put("medulla", stem & (Z < -43))
    put("accumbens", np.isin(ho, [11, 21]))
    put("ventricle", np.isin(ho, [3, 14]) & (aal == 0))
    put("cc", np.isin(jhu, [3, 4, 5]) & (aal == 0))
    put("fornix", np.isin(jhu, [6, 39, 40]) & (aal == 0) & ~np.isin(ho, [3, 14]))
    put("whitematter", np.isin(ho, [1, 12]), only_empty=True)
    for n, blobs in BLOBS.items():
        m = np.zeros(shp, bool)
        for (cx, cy, cz), (rx, ry, rz) in blobs: m |= ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 + ((Z - cz) / rz) ** 2 <= 1
        if n == "hypothalamus": m &= ~np.isin(aal, [77, 78])
        put(n, m)
    print("atoms", len(atoms))

    # 배경 MRI (nilearn 내장 MNI152 2009) → 같은 격자로
    from nilearn import datasets, image
    t1 = image.resample_to_img(datasets.load_mni152_template(resolution=1), aal_i, interpolation="continuous")
    T = np.asarray(t1.dataobj).astype(np.float32); T = np.clip(T / np.percentile(T[T > 0], 99.5), 0, 1)
    brain = (L > 0) | (T > 0.25)
    brain = ndi.binary_closing(ndi.binary_fill_holes(L > 0), iterations=2)

    os.makedirs(os.path.join(OUT, "img"), exist_ok=True)
    SC = 2  # 그림 배율 (1mm = 2px)

    def shade(depth, valid):
        d = ndi.gaussian_filter(np.where(valid, depth, np.nan_to_num(depth[valid].max() if valid.any() else 0)), 1.2)
        gy, gx = np.gradient(d)
        n = np.dstack([-gx, -gy, np.ones_like(d) * 1.1]); n /= np.linalg.norm(n, axis=2, keepdims=True)
        lt = np.array([-0.45, -0.55, 0.7]); lt /= np.linalg.norm(lt)
        s = np.clip((n * lt).sum(2), 0, 1)
        near = (d - d[valid].min()) / max(1e-6, (d[valid].max() - d[valid].min())) if valid.any() else d
        g = 0.32 + 0.6 * s - 0.18 * near
        return np.where(valid, np.clip(g, 0, 1), np.nan)

    def proj(axis, from_end, keep):
        """axis 따라 처음 만나는 조각 → (라벨 2D, 깊이 2D)"""
        lab = np.where(keep, L, 0)
        if from_end: lab = np.flip(lab, axis)
        nz = lab > 0
        first = np.argmax(nz, axis=axis); has = nz.any(axis=axis)
        lab2 = np.take_along_axis(lab, np.expand_dims(first, axis), axis).squeeze(axis)
        return np.where(has, lab2, 0), np.where(has, first, 0).astype(np.float32), has

    view_out = []
    for vid, vname, kind, note in VIEWS:
        if vid == "lat":   # 왼쪽(x<0)에서: i 큰 쪽이 x 작은 쪽 → from_end
            keep = (X < 0) & np.isin(L, [atoms.index(a) + 1 for a in atoms if not a.startswith(("whitematter", "ventricle"))])
            lab, dep, has = proj(0, True, keep)          # (j=y, k=z)
            lab, dep, has = lab.T[::-1, ::-1], dep.T[::-1, ::-1], has.T[::-1, ::-1]   # 행 = 위→아래(z), 열 = 앞→뒤(y)
        elif vid == "med":  # x=-1 에서 왼쪽으로 (i: x=-1 → i=91)
            keep = (X <= -1)
            sub = np.where(keep, L, 0)[91:, :, :]       # i 91.. = x -1 .. -90
            nz = sub > 0; first = np.argmax(nz, 0); has = nz.any(0)
            lab = np.take_along_axis(sub, first[None], 0)[0]; lab = np.where(has, lab, 0); dep = first.astype(np.float32)
            lab, dep, has = lab.T[::-1, ::-1], dep.T[::-1, ::-1], has.T[::-1, ::-1]
        elif vid == "inf":  # 아래(z 작은 쪽)에서 위로, 소뇌·뇌간·뇌하수체 빼고
            drop = [atoms.index(a) + 1 for a in atoms if a.split(":")[0] in ("cerebellum", "midbrain", "pons", "medulla", "lc", "raphe", "pituitary", "sn", "vta")]
            keep = ~np.isin(L, drop) & (L > 0)
            lab, dep, has = proj(2, False, keep)        # (i=x, j=y)
            lab, dep, has = lab.T[::-1, :], dep.T[::-1, :], has.T[::-1, :]   # 행 = 앞→뒤, 열 = i (x +90 → -90: 화면 왼쪽 = 오른쪽 뇌)
        else:
            if vid == "cor": j0 = int(round((-6 - aff[1, 3]) / aff[1, 1])); lab = L[:, j0, :].T[::-1, :]; bgT = T[:, j0, :].T[::-1, :]
            elif vid == "cor2": j0 = int(round((-22 - aff[1, 3]) / aff[1, 1])); lab = L[:, j0, :].T[::-1, :]; bgT = T[:, j0, :].T[::-1, :]
            else: k0 = int(round((6 - aff[2, 3]) / aff[2, 2])); lab = L[:, :, k0].T[::-1, :]; bgT = T[:, :, k0].T[::-1, :]
            has = lab > 0; dep = None
        # 자르기
        rows, cols = np.where(has if dep is not None else (has | (bgT > 0.12)))
        r0, r1, c0, c1 = max(rows.min() - 4, 0), rows.max() + 5, max(cols.min() - 4, 0), cols.max() + 5
        lab = lab[r0:r1, c0:c1]; hv = has[r0:r1, c0:c1]
        if dep is not None:
            g = shade(dep[r0:r1, c0:c1], hv)
            rgba = np.zeros(g.shape + (4,), np.uint8)
            rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = np.nan_to_num(g * 255).astype(np.uint8); rgba[..., 3] = np.where(hv, 255, 0)
        else:
            bt = bgT[r0:r1, c0:c1]
            rgba = np.zeros(bt.shape + (4,), np.uint8); v8 = (np.clip(bt * 1.08, 0, 1) * 255).astype(np.uint8)
            rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = v8; rgba[..., 3] = np.where(bt > 0.08, 255, 0)
        im = Image.fromarray(rgba, "RGBA").resize((lab.shape[1] * SC, lab.shape[0] * SC), Image.LANCZOS)
        im.save(os.path.join(OUT, "img", vid + ".webp"), "WEBP", quality=80, method=6)
        # 조각 경로
        paths = {}
        for a in np.unique(lab):
            if a == 0: continue
            m = ndi.zoom((lab == a).astype(np.float32), SC, order=1)
            m = ndi.gaussian_filter(m, 0.9)
            if (m > 0.5).sum() < 6: continue
            d = []
            for c in measure.find_contours(np.pad(m, 1), 0.5):
                c = measure.approximate_polygon(c - 1, 0.7)
                if len(c) < 4: continue
                d.append("M" + "L".join(f"{p[1]:.0f} {p[0]:.0f}" for p in c) + "Z")
            if d: paths[atoms[a - 1]] = ["".join(d), int((lab == a).sum())]
        # 테두리 (뇌 밖 윤곽)
        out_m = ndi.gaussian_filter(ndi.zoom(hv.astype(np.float32), SC, order=1), 1.0)
        oc = [measure.approximate_polygon(c - 1, 0.8) for c in measure.find_contours(np.pad(out_m, 1), 0.5) if len(c) > 30]
        outline = "".join("M" + "L".join(f"{p[1]:.0f} {p[0]:.0f}" for p in c) + "Z" for c in oc)
        view_out.append({"id": vid, "name": vname, "kind": kind, "note": note, "w": lab.shape[1] * SC, "h": lab.shape[0] * SC,
                         "img": "img/" + vid + ".webp", "outline": outline, "atoms": paths})
        print(vid, lab.shape, len(paths), "atoms", sum(len(p) for p in paths.values()) // 1024, "KB")
    json.dump({"v": 1, "atoms": atoms, "views": view_out}, open(os.path.join(OUT, "atlas.json"), "w"), ensure_ascii=False, separators=(",", ":"))

    # ───── 3D ─────
    import trimesh
    meta = []; buf = bytearray()
    budget = {"cerebellum": 3200, "whitematter": 0, "ventricle": 1600, "cc": 900}
    for idx, a in enumerate(atoms):
        base = a.split(":")[0]
        if budget.get(base, 1) == 0: continue
        m = (L == idx + 1)
        if m.sum() < 8: continue
        sl = ndi.find_objects(m.astype(np.int8))[0]
        sl = tuple(slice(max(s.start - 3, 0), s.stop + 3) for s in sl)
        sm = ndi.gaussian_filter(m[sl].astype(np.float32), 1.0 if m.sum() > 400 else 0.6)
        lvl = 0.5 if sm.max() > 0.55 else sm.max() * 0.6
        v, f, _, _ = measure.marching_cubes(sm, lvl)
        v += np.array([s.start for s in sl])
        tm = trimesh.Trimesh(v, f, process=True)
        trimesh.smoothing.filter_taubin(tm, iterations=8)
        tgt = budget.get(base) or max(160, min(2400, int(len(tm.faces) * 0.12)))
        if len(tm.faces) > tgt:
            import fast_simplification
            vv, ff = fast_simplification.simplify(tm.vertices.astype(np.float32), tm.faces.astype(np.int64), 1 - tgt / len(tm.faces))
            tm = trimesh.Trimesh(vv, ff, process=True)
        vox = tm.vertices
        mni = np.c_[aff[0, 0] * vox[:, 0] + aff[0, 3], aff[1, 1] * vox[:, 1] + aff[1, 3], aff[2, 2] * vox[:, 2] + aff[2, 3]]
        q = np.round(mni * 10).astype("<i2"); fi = tm.faces.astype("<u2")
        meta.append({"a": a, "vo": len(buf), "vn": len(q), "fo": len(buf) + q.nbytes, "fn": len(fi)})
        buf += q.tobytes(); buf += fi.tobytes()
        if len(buf) % 4: buf += b"\0" * (4 - len(buf) % 4)
    open(os.path.join(OUT, "mesh.bin"), "wb").write(bytes(buf))
    json.dump({"v": 1, "scale": 0.1, "parts": meta}, open(os.path.join(OUT, "mesh.json"), "w"), separators=(",", ":"))
    print("mesh", len(meta), "parts", len(buf) // 1024, "KB", sum(x["fn"] for x in meta), "tris")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--text", action="store_true"); ap.add_argument("--atlas")
    a = ap.parse_args()
    text_only()
    if a.atlas: build_atlas(a.atlas)
