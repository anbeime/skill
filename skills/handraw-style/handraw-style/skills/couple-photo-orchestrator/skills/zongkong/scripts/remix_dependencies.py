#!/usr/bin/env python3
"""Resolve downstream invalidation for one-variable remix requests."""
from __future__ import annotations
import argparse, json

GRAPH={
 "location":{"always":["scene","props","pose_shot","share_card","render"],"conditional":["hairstyle","makeup","wardrobe"]},
 "era":{"always":["wardrobe","hairstyle","makeup","scene","props","pose_shot","share_card","render"],"conditional":[]},
 "worldview":{"always":["wardrobe","hairstyle","makeup","scene","props","pose_shot","share_card","render"],"conditional":[]},
 "wardrobe":{"always":["hairstyle","makeup","pose_shot","share_card","render"],"conditional":["props"]},
 "hairstyle":{"always":["makeup","pose_shot","render"],"conditional":["share_card"]},
 "makeup":{"always":["pose_shot","render"],"conditional":["share_card"]},
 "relationship":{"always":["pose_emotion","pose_shot","share_card","render"],"conditional":["wardrobe"]},
 "color":{"always":["wardrobe_palette","hairstyle","makeup","lighting","pose_shot","share_card","render"],"conditional":[]},
 "photography_style":{"always":["lighting","composition","pose_shot","share_card","render"],"conditional":["makeup"]},
}
ALIASES={"地点":"location","年代":"era","世界观":"worldview","服装":"wardrobe","发型":"hairstyle","妆容":"makeup","关系":"relationship","色彩":"color","摄影气质":"photography_style","摄影风格":"photography_style"}
def resolve(target):
    key=ALIASES.get(target,target)
    if key not in GRAPH: raise KeyError(key)
    return {"target":key,**GRAPH[key]}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('target'); a=ap.parse_args(); print(json.dumps(resolve(a.target),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
