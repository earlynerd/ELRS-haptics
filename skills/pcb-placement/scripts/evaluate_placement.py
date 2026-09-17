"""Read-only placement metrics. Run with KiCad's bundled python.exe.

The pad-centre Euclidean MST is a placement proxy, not a route estimate.
Unconnected-pair span estimates use fresh KiCad DRC plus pad/track anchors.
"""
import argparse
from collections import defaultdict, Counter
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys


def metrics(edges):
    values=sorted(e['length_mm'] for e in edges)
    return dict(count=len(values), total_mm=sum(values),
                mean_mm=statistics.mean(values) if values else None,
                median_mm=statistics.median(values) if values else None,
                p95_mm=values[max(0,math.ceil(.95*len(values))-1)] if values else None,
                max_mm=values[-1] if values else None)


def mst(nodes, net):
    """Deterministic Prim tree on every copper pad centre; O(n^2) time.

    Coincident pads remain separate nodes and contribute zero-length edges.
    Same-footprint and duplicate-number pads are not silently contracted.
    """
    nodes=sorted(nodes,key=lambda n:n['id'])
    if len(nodes)<2:return []
    used={0}; best={j:(math.dist(nodes[0]['xy'],nodes[j]['xy']),0) for j in range(1,len(nodes))}
    edges=[]
    while best:
        j=min(best,key=lambda j:(best[j][0],nodes[j]['id'],nodes[best[j][1]]['id']))
        distance,i=best.pop(j)
        edges.append(dict(net=net,a=nodes[i],b=nodes[j],length_mm=distance,
                          same_footprint=nodes[i]['reference']==nodes[j]['reference']))
        used.add(j)
        for k in best:
            candidate=(math.dist(nodes[j]['xy'],nodes[k]['xy']),j)
            if candidate<best[k]:best[k]=candidate
    return edges


def fingerprint(nodes):
    # Deliberately exclude positions/rotations so placement variants compare.
    topology=sorted((n['id'],n['reference'],n['pad'],n['net']) for n in nodes)
    return hashlib.sha256(json.dumps(topology).encode()).hexdigest()


def compare(current, previous):
    if current['topology_sha256']!=previous['topology_sha256']:
        return {'comparable':False,'reason':'Pad identities or net assignments changed.'}
    if current['exclude_net_patterns']!=previous['exclude_net_patterns']:
        return {'comparable':False,'reason':'Net filters differ.'}
    result={'comparable':True}
    for key in ['placement_mst','remaining_airwires']:
        a=current[key]['summary'];b=previous[key]['summary']
        result[key]={k:(a[k]-b[k] if a[k] is not None and b[k] is not None else None) for k in a}
    return result


def summarize(edges):
    groups=defaultdict(list);refs=defaultdict(list)
    for e in edges:
        groups[e['net']].append(e)
        for ref in {e['a']['reference'],e['b']['reference']}:
            if ref:refs[ref].append(e)
    return dict(summary=metrics(edges),by_net={n:metrics(v) for n,v in sorted(groups.items())},
                by_component={r:metrics(v) for r,v in sorted(refs.items())},
                longest=sorted(edges,key=lambda e:(-e['length_mm'],e['net']))[:20],edges=edges)


def write_markdown(report,path):
    fmt=lambda v:'—' if v is None else f'{v:.3f}'
    lines=['# Placement evaluation','',f"Saved board: `{report['board']}`",
           f"SHA-256: `{report['board_sha256']}`",'',
           'Straight-line XY distances in mm; these are not routed lengths.',
           f"Excluded net regexes: `{report['exclude_net_patterns']}`",'',
           '| Measure | Spans | Total mm | Mean mm | Median mm | P95 mm | Max mm |',
           '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for key,label in [('placement_mst','Pad-centre MST (routing independent)'),('remaining_airwires','Remaining unconnected-pair spans')]:
        s=report[key]['summary'];lines.append(f"| {label} | {s['count']} | "+' | '.join(fmt(s[k]) for k in ['total_mm','mean_mm','median_mm','p95_mm','max_mm'])+' |')
    lines+=['','## Longest placement-tree connections','',
            '| Net | From | To | mm |','| --- | --- | --- | ---: |']
    for e in report['placement_mst']['longest'][:12]:
        label=lambda n:f"{n['reference']}.{n['pad']}"
        lines.append(f"| {e['net']} | {label(e['a'])} | {label(e['b'])} | {e['length_mm']:.3f} |")
    lines+=['','## Largest net totals','','| Net | Spans | Total mm | Mean mm |','| --- | ---: | ---: | ---: |']
    for net,s in sorted(report['placement_mst']['by_net'].items(),key=lambda x:-x[1]['total_mm'])[:12]:
        lines.append(f"| {net} | {s['count']} | {s['total_mm']:.3f} | {fmt(s['mean_mm'])} |")
    lines+=['','## Native board checks','',f"DRC categories: `{report['drc_categories']}`",
            f"Unconnected pairs (all nets): {report['native_unconnected_count']}",
            '', '## Interpretation','',
            '- Compare total and mean only with unchanged pad/net topology and the same filters.',
            '- The MST ignores tracks, planes, obstacles and layers. It includes same-footprint connections and duplicate pad numbers; these are tagged in JSON.',
            '- Remaining spans use native DRC item pairs with nearest pad-centre/track-end anchors. They approximate the displayed ratsnest, not exact copper-edge gaps. Unsupported endpoint types fail explicitly. Saved zone fill is used; unsaved edits and unfilled plane updates are not included.',
            '- Remaining-span mean can increase as short connections are routed. It is not a stable placement score.',
            '- Ground and power planes can dominate the all-net score. Exclude only explicitly named nets and retain the all-net report for context.',
            '- Lower distance does not prove routability or electrical quality. Check shorts, courtyards, board edges, critical loops, decoupling and antenna keepouts separately.',
            '- Component totals count incident tree edges; totals across components double-count shared edges and are not a movement recommendation.']
    if 'comparison' in report:lines+=['','## Baseline comparison','', '```json',json.dumps(report['comparison'],indent=2),'```']
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('board',type=Path)
    ap.add_argument('--out',type=Path,required=True,help='Report directory, never the source board')
    ap.add_argument('--exclude-net',action='append',default=[],help='Regex searched against full net name; repeatable')
    ap.add_argument('--compare',type=Path,help='Earlier placement.json; read before output is written')
    ap.add_argument('--kicad-cli',type=Path,default=Path(sys.executable).with_name('kicad-cli.exe'))
    args=ap.parse_args();patterns=[re.compile(x) for x in args.exclude_net]
    previous=json.loads(args.compare.read_text()) if args.compare else None
    import pcbnew as p
    boardpath=args.board.resolve();raw=boardpath.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    board=p.LoadBoard(str(boardpath));args.out.mkdir(parents=True,exist_ok=True)
    nodes=[];by_net=defaultdict(list);lookup={}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            net=pad.GetNetname()
            if pad.GetNetCode()<=0 or not pad.GetLayerSet().CuStack():continue
            n=dict(id=pad.m_Uuid.AsString(),reference=fp.GetReference(),pad=pad.GetNumber(),net=net,
                   xy=[p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y)],layer=fp.GetLayerName())
            nodes.append(n);lookup[n['id']]=n
            if not any(r.search(net) for r in patterns):by_net[net].append(n)
    edges=[e for net,group in sorted(by_net.items()) for e in mst(group,net)]
    item_nets={n['id']:n['net'] for n in nodes}
    anchors={n['id']:[n['xy']] for n in nodes}
    for item in board.GetTracks():
        item_nets[item.m_Uuid.AsString()]=item.GetNetname()
        anchors[item.m_Uuid.AsString()]=[[p.ToMM(v.x),p.ToMM(v.y)] for v in [item.GetStart(),item.GetEnd()]]
    env=os.environ.copy()
    env.setdefault('KICAD_DOCUMENTS_HOME',str(args.out.resolve()/'runtime/documents'))
    env.setdefault('KICAD_CONFIG_HOME',str(args.out.resolve()/'runtime/config'))
    for key in ['KICAD_DOCUMENTS_HOME','KICAD_CONFIG_HOME']:Path(env[key]).mkdir(parents=True,exist_ok=True)
    drcpath=args.out.resolve()/'drc.json'
    cmd=[str(args.kicad_cli),'pcb','drc','--format','json','-o',str(drcpath),str(boardpath)]
    result=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=180)
    (args.out/'drc.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError(f'KiCad DRC failed: see {args.out}/drc.log')
    drc=json.loads(drcpath.read_text());air=[]
    for violation in drc['unconnected_items']:
        items=violation['items']
        if len(items)!=2:raise ValueError('Unexpected DRC endpoint count')
        endpoints=[];netnames=set()
        for item in items:
            ident=item['uuid'];known=lookup.get(ident)
            if ident in item_nets:netnames.add(item_nets[ident])
            endpoints.append(dict(id=ident,reference=known['reference'] if known else '',
                                  pad=known['pad'] if known else '',description=item['description'],
                                  xy=[item['pos']['x'],item['pos']['y']]))
        if len(netnames)!=1:raise ValueError(f'Cannot resolve DRC net: {items}')
        net=netnames.pop()
        if any(r.search(net) for r in patterns):continue
        if any(n['id'] not in anchors for n in endpoints):
            raise ValueError('Unsupported DRC endpoint (e.g. zone); cannot measure reliably from its report position.')
        # A DRC track item's reported position is its START, not necessarily the
        # airwire anchor. Resolve nearest endpoint pair instead of measuring it.
        a,b=min(((a,b) for a in anchors[endpoints[0]['id']] for b in anchors[endpoints[1]['id']]),key=lambda pair:math.dist(*pair))
        endpoints[0]['xy']=a;endpoints[1]['xy']=b
        air.append(dict(net=net,a=endpoints[0],b=endpoints[1],length_mm=math.dist(endpoints[0]['xy'],endpoints[1]['xy'])))
    assert hashlib.sha256(boardpath.read_bytes()).hexdigest()==digest,'Board changed during evaluation; rerun on a stable saved board'
    report=dict(schema_version=1,board=str(boardpath),board_sha256=digest,kicad_version=p.GetBuildVersion(),
                topology_sha256=fingerprint(nodes),exclude_net_patterns=args.exclude_net,
                footprint_count=len(list(board.GetFootprints())),netted_copper_pad_count=len(nodes),
                placement_mst=summarize(edges),remaining_airwires=summarize(air),
                native_unconnected_count=len(drc['unconnected_items']),
                drc_categories=dict(Counter(x['type'] for x in drc['violations'])))
    if previous:report['comparison']=compare(report,previous)
    (args.out/'placement.json').write_text(json.dumps(report,indent=2)+'\n')
    write_markdown(report,args.out/'placement.md')
    print(json.dumps({k:report[k]['summary'] for k in ['placement_mst','remaining_airwires']},indent=2))
    print(args.out/'placement.md')


if __name__=='__main__':main()
