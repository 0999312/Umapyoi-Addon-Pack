import sys
import tempfile
from pathlib import Path
import shutil
import os
import tomllib
import tomli_w
import glob
import json
import zipfile

with tempfile.TemporaryDirectory() as tmp_dir:
    tmp_path = Path(tmp_dir)
    for file in os.listdir():
        if file.startswith(".git"):
            continue
        if file == Path(__file__).resolve().name:
            continue
        if file == "META-INF":
            srpath = tmp_path / "META-INF"
            srpath.mkdir()
            for fn in os.listdir("META-INF"):
                fipath = Path("META-INF") / fn
                if fn == "mods.toml":
                    data = tomllib.load(open(fipath, "rb"))
                    data["loaderVersion"] = "[4,)"
                    for v in data["mods"]:
                        if v["modId"] == "umapyoi_addon":
                            v["version"] = v["version"].replace("-1.20.1", "-1.21.1")
                    for k in data["dependencies"]:
                        for v in data["dependencies"][k]:
                            if v["modId"] == "forge":
                                v["modId"] = "neoforge"
                                v["versionRange"] = "[21.0,)"
                            if v["modId"] == "umapyoi":
                                del v["versionRange"]
                            mandatory = v.get("mandatory", True)
                            del v["mandatory"]
                            v["type"] = "required" if mandatory else "optional"
                    with open(srpath / "neoforge.mods.toml", "wb") as wf:
                        tomli_w.dump(data, wf)
                elif fipath.is_dir():
                    shutil.copytree(fipath, srpath / fn, dirs_exist_ok = True)
                else:
                    shutil.copy2(fipath, srpath / fn)
        elif file == "data":
            dstpath = tmp_path / "data"
            dstpath.mkdir()
            srcpath = Path("data")
            for namespace in os.listdir("data"):
                dpath = dstpath / namespace
                dpath.mkdir()
                spath = srcpath / namespace
                for fn in os.listdir(spath):
                    if fn in ["recipes", "loot_tables", "advancements", "predicates", "item_modifiers", "structures", "functions"]:
                        shutil.copytree(spath / fn, dpath / fn[:-1], dirs_exist_ok = True)
                        if fn == "recipes":
                            ref = dpath / fn[:-1]
                            for i in os.listdir(ref):
                                if i.endswith(".json"):
                                    raw = json.load(open(ref / i))
                                    if raw["type"] in ["minecraft:crafting_shaped", "minecraft:crafting_shapeless", "minecraft:smithing_transform"]:
                                        item = raw["result"]["item"]
                                        del raw["result"]["item"]
                                        raw["result"]["id"] = item
                                    elif raw["type"] in ["minecraft:smelting", "minecraft:blasting", "minecraft:smoking", "minecraft:campfire_cooking"]:
                                        raw["result"] = {"id": raw["result"]}
                                    elif raw["type"] == "minecraft:stonecutting":
                                        cnt = raw.get("count", 1)
                                        try:
                                            del raw["count"]
                                        except KeyError:
                                            pass
                                        raw["result"] = {"id": raw["result"], "count": cnt}
                                    with open(ref / i, "w") as wr:
                                        json.dump(raw, wr)
                    elif fn == "tags":
                        (dpath / fn).mkdir()
                        for tag_criteria in os.listdir(spath / fn):
                            if tag_criteria in ["items", "blocks", "entity_types", "fluids", "game_events", "functions"]:
                                shutil.copytree(spath / fn / tag_criteria, dpath / fn / tag_criteria[:-1], dirs_exist_ok = True)
                            elif (spath / fn / tag_criteria).is_dir():
                                shutil.copytree(spath / fn / tag_criteria, dpath / fn / tag_criteria, dirs_exist_ok = True)
                            else:
                                shutil.copy2(spath / fn / tag_criteria, dpath / fn / tag_criteria)
                    elif (spath / fn).is_dir():
                        shutil.copytree(spath / fn, dpath / fn, dirs_exist_ok = True)
                    else:
                        shutil.copy2(spath / fn, dpath / fn)
        elif Path(file).is_dir():
            shutil.copytree(file, tmp_path / file, dirs_exist_ok = True)
        else:
            shutil.copy2(file, tmp_path / file)
    assert sys.argv[-1].endswith(".jar")
    with zipfile.ZipFile(sys.argv[-1], "w", compression = zipfile.ZIP_DEFLATED) as zf:
        for file in tmp_path.rglob("*"):
            if file.is_file():
                zf.write(file, arcname = file.relative_to(tmp_path))