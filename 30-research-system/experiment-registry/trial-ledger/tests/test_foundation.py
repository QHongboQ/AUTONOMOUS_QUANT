import os,tempfile,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from aq_trial_ledger.canonical import *
from aq_trial_ledger.storage import Ledger,LedgerError
S={"generator":"qlib","learning_rate":"0.10","when":"x"}
class CanonicalTests(unittest.TestCase):
 def test_vectors(self):
  b,h=hash_research_spec(S,decimal_fields={"learning_rate"});self.assertEqual(b,b'{"canonicalization_version":"AQ_RESEARCH_SPEC_CANONICAL_V1","research_spec":{"generator":"qlib","learning_rate":"0.1","when":"x"}}');self.assertEqual(h,"afd95241c4ede114840cd6013d602b99c3de3f8d83e1f42e1be4e9d1ea4cc456")
  self.assertEqual(canonicalize_research_spec({"b":1,"a":2}),canonicalize_research_spec({"a":2,"b":1}))
  self.assertIn("é".encode(),canonicalize_research_spec({"x":"é"}));self.assertIn(b'\\u000a',canonicalize_research_spec({"x":"\n"}))
 def test_negative(self):
  for x in [{"x":float('nan')},{"x":"\ud800"},{"trial_id":"x"}]:
   with self.assertRaises(CanonicalizationError):canonicalize_research_spec(x)
  with self.assertRaises(CanonicalizationError):parse_json_strict('{"x":1,"x":2}')
class LedgerTests(unittest.TestCase):
 def test_registration_chain_snapshot_backup(self):
  with tempfile.TemporaryDirectory() as d:
   p=os.path.join(d,"x.db");l=Ledger(p);l.init();t=l.register("human:owner","a",S,decimal_fields={"learning_rate"});self.assertEqual(t,l.register("human:owner","a",S,decimal_fields={"learning_rate"}));self.assertTrue(l.verify_global_chain());a=l.anchor("human:owner");self.assertEqual(a["manifest_sha256"],__import__('hashlib').sha256(canonicalize_anchor_payload(a["payload"])).hexdigest());b=os.path.join(d,"b.db");l.backup_to(b);copy=Ledger(b);self.assertTrue(copy.verify_global_chain());copy.close();l.close()
 def test_guards(self):
  with tempfile.TemporaryDirectory() as d:
   l=Ledger(os.path.join(d,"x.db"));l.init();l.register("human:owner","a",S,decimal_fields={"learning_rate"})
   with self.assertRaises(LedgerError):l.register("human:owner","a",{"generator":"other"})
   with self.assertRaises(Exception):l.db.execute("DELETE FROM trials")
   l.close()
if __name__=='__main__':unittest.main()
