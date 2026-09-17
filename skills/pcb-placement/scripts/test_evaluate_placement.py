"""Metric invariants and native KiCad routed/unrouted integration check."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from evaluate_placement import mst,metrics,fingerprint,compare


def node(i,x,y):
    return dict(id=str(i),reference='J'+str(i),pad='1',net='SIGNAL',xy=[x,y])


class MetricsTests(unittest.TestCase):
    def test_triangle_not_all_pairs(self):
        edges=mst([node(1,0,0),node(2,3,0),node(3,0,4)],'SIGNAL')
        self.assertEqual(metrics(edges)['total_mm'],7)
        self.assertEqual(len(edges),2)

    def test_order_and_translation_invariant(self):
        ns=[node(1,0,0),node(2,1,0),node(3,1,1),node(4,0,1)]
        self.assertEqual(mst(ns,'SIGNAL'),mst(ns[::-1],'SIGNAL'))
        shifted=[dict(n,xy=[n['xy'][0]+12,n['xy'][1]-8]) for n in ns]
        self.assertEqual(metrics(mst(ns,'SIGNAL')),metrics(mst(shifted,'SIGNAL')))
        self.assertEqual(fingerprint(ns),fingerprint(shifted))

    def test_coincident_and_empty(self):
        self.assertEqual(metrics(mst([node(1,0,0),node(2,0,0)],'S'))['total_mm'],0)
        self.assertIsNone(metrics([])['mean_mm'])

    def test_comparison_guards(self):
        s=metrics([])
        a=dict(topology_sha256='a',exclude_net_patterns=[],placement_mst={'summary':s},remaining_airwires={'summary':s})
        self.assertTrue(compare(a,a)['comparable'])
        self.assertFalse(compare(a,dict(a,topology_sha256='b'))['comparable'])
        self.assertFalse(compare(a,dict(a,exclude_net_patterns=['GND']))['comparable'])

    def test_native_route_does_not_change_placement_score(self):
        import pcbnew as p
        with tempfile.TemporaryDirectory(prefix='placement-test-') as td:
            td=Path(td);board=p.BOARD();net=p.NETINFO_ITEM(board,'SIGNAL');board.Add(net)
            for i,x in [(1,10),(2,15)]:
                fp=p.FOOTPRINT(board);fp.SetReference('J'+str(i));board.Add(fp)
                pad=p.PAD(fp);pad.SetNumber('1');pad.SetAttribute(p.PAD_ATTRIB_SMD)
                pad.SetShape(p.PAD_SHAPE_RECT);pad.SetSize(p.VECTOR2I(p.FromMM(.5),p.FromMM(.5)))
                layers=p.LSET();layers.AddLayer(p.F_Cu)
                pad.SetLayerSet(layers);pad.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(10)))
                pad.SetNet(net);fp.Add(pad)
            file=td/'fixture.kicad_pcb';p.SaveBoard(str(file),board)
            script=Path(__file__).with_name('evaluate_placement.py')
            def run(name):
                result=subprocess.run([sys.executable,str(script),str(file),'--out',str(td/name)],capture_output=True,text=True,timeout=60)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                return json.loads((td/name/'placement.json').read_text())
            before=run('unrouted')
            track=p.PCB_TRACK(board);track.SetStart(p.VECTOR2I(p.FromMM(10),p.FromMM(10)))
            track.SetEnd(p.VECTOR2I(p.FromMM(12),p.FromMM(10)));track.SetWidth(p.FromMM(.2))
            track.SetLayer(p.F_Cu);track.SetNet(net);board.Add(track);p.SaveBoard(str(file),board)
            partial=run('partial')
            self.assertEqual(partial['remaining_airwires']['summary']['count'],1)
            self.assertAlmostEqual(partial['remaining_airwires']['summary']['total_mm'],3)
            self.assertEqual(before['placement_mst']['summary'],partial['placement_mst']['summary'])
            track.SetEnd(p.VECTOR2I(p.FromMM(15),p.FromMM(10)));p.SaveBoard(str(file),board)
            after=run('routed')
            self.assertEqual(before['remaining_airwires']['summary']['count'],1)
            self.assertAlmostEqual(before['remaining_airwires']['summary']['total_mm'],5)
            self.assertEqual(after['remaining_airwires']['summary']['count'],0)
            self.assertEqual(before['placement_mst']['summary'],after['placement_mst']['summary'])


if __name__=='__main__':unittest.main()
