from __future__ import annotations
import hashlib,json,sqlite3,threading,uuid
from contextlib import contextmanager
from datetime import datetime,timezone
from .canonical import hash_research_spec,canonicalize_anchor_payload
ZERO="0"*64
def now():return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
class LedgerError(ValueError):pass
class Ledger:
 def __init__(self,path):
  self.db=sqlite3.connect(path,check_same_thread=False);self.db.row_factory=sqlite3.Row;self.lock=threading.RLock();self.db.execute("PRAGMA foreign_keys=ON");self.db.execute("PRAGMA busy_timeout=5000")
 def close(self): self.db.close()
 def init(self,owner="human:owner"):
  with self.lock,self.db:
   self.db.executescript('''CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY,v TEXT NOT NULL);CREATE TABLE IF NOT EXISTS actors(id TEXT PRIMARY KEY,typ TEXT NOT NULL);CREATE TABLE IF NOT EXISTS capabilities(actor TEXT,cap TEXT,active INTEGER,PRIMARY KEY(actor,cap),FOREIGN KEY(actor) REFERENCES actors(id));CREATE TABLE IF NOT EXISTS specs(hash TEXT PRIMARY KEY,blob BLOB NOT NULL);CREATE TABLE IF NOT EXISTS trials(id TEXT PRIMARY KEY,hash TEXT NOT NULL,actor TEXT NOT NULL,idem TEXT NOT NULL,request_hash TEXT NOT NULL,FOREIGN KEY(hash) REFERENCES specs(hash),FOREIGN KEY(actor) REFERENCES actors(id),UNIQUE(actor,idem));CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY,trial TEXT,typ TEXT NOT NULL,actor TEXT NOT NULL,payload TEXT NOT NULL,prev TEXT NOT NULL,hash TEXT NOT NULL);CREATE TRIGGER IF NOT EXISTS no_trial_update BEFORE UPDATE ON trials BEGIN SELECT RAISE(ABORT,'immutable');END;CREATE TRIGGER IF NOT EXISTS no_trial_delete BEFORE DELETE ON trials BEGIN SELECT RAISE(ABORT,'immutable');END;CREATE TRIGGER IF NOT EXISTS no_event_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'immutable');END;CREATE TRIGGER IF NOT EXISTS no_event_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'immutable');END;''')
   if self.db.execute("SELECT 1 FROM meta WHERE k='ledger_id'").fetchone():raise LedgerError("initialized")
   lid=str(uuid.uuid4());self.db.executemany("INSERT INTO meta VALUES(?,?)",[("ledger_id",lid),("schema_version","1")]);self.db.execute("INSERT INTO actors VALUES(?,?)",(owner,"HUMAN_OWNER"));self.db.execute("INSERT INTO capabilities VALUES(?,?,1)",(owner,"TRIAL_REGISTER"));self.event(None,"GENESIS",owner,{"ledger_id":lid})
   return lid
 def event(self,trial,typ,actor,payload):
  row=self.db.execute("SELECT seq,hash FROM events ORDER BY seq DESC LIMIT 1").fetchone();seq=(row["seq"]+1 if row else 1);prev=row["hash"] if row else ZERO; p=json.dumps(payload,sort_keys=True,separators=(",",":"));h=hashlib.sha256(f"{seq}|{prev}|{typ}|{actor}|{trial}|{p}".encode()).hexdigest();self.db.execute("INSERT INTO events VALUES(?,?,?,?,?,?,?)",(seq,trial,typ,actor,p,prev,h));return seq,h
 def register(self,actor,idem,spec,*,decimal_fields=(),kind="INDEPENDENT_EVALUATION"):
  with self.lock,self.db:
   if not self.db.execute("SELECT 1 FROM capabilities WHERE actor=? AND cap='TRIAL_REGISTER' AND active=1",(actor,)).fetchone():raise LedgerError("unauthorized")
   b,h=hash_research_spec(spec,decimal_fields=decimal_fields);req=hashlib.sha256((h+kind).encode()).hexdigest();old=self.db.execute("SELECT id,request_hash FROM trials WHERE actor=? AND idem=?",(actor,idem)).fetchone()
   if old:
    if old["request_hash"]!=req:raise LedgerError("idempotency conflict")
    return old["id"]
   self.db.execute("INSERT OR IGNORE INTO specs VALUES(?,?)",(h,b));tid=str(uuid.uuid4());self.db.execute("INSERT INTO trials VALUES(?,?,?,?,?)",(tid,h,actor,idem,req));self.event(tid,"TRIAL_REGISTERED",actor,{"research_hash":h,"kind":kind});return tid
 def verify_global_chain(self):
  prev=ZERO
  for r in self.db.execute("SELECT * FROM events ORDER BY seq"):
   p=f"{r['seq']}|{prev}|{r['typ']}|{r['actor']}|{r['trial']}|{r['payload']}";h=hashlib.sha256(p.encode()).hexdigest()
   if r['prev']!=prev or r['hash']!=h:return False
   prev=h
  return True
 def snapshot(self):
  if self.db.execute("PRAGMA integrity_check").fetchone()[0]!="ok" or not self.verify_global_chain():raise LedgerError("snapshot blocked")
  rows=tuple(tuple(r) for r in self.db.execute("SELECT seq,trial,typ,actor,payload,hash FROM events ORDER BY seq"));end=rows[-1][-1] if rows else ZERO;blob=json.dumps(rows,separators=(",",":"));return {"as_of_ledger_sequence":len(rows),"global_event_hash":end,"content_hash":hashlib.sha256(blob.encode()).hexdigest(),"events":rows}
 def anchor(self,actor):
  s=self.snapshot();p={"ledger_id":self.db.execute("SELECT v FROM meta WHERE k='ledger_id'").fetchone()[0],"as_of_ledger_sequence":s["as_of_ledger_sequence"],"global_event_hash":s["global_event_hash"],"schema_version":"1","created_at":now(),"created_by":actor,"manifest_schema_version":"1"};return {"payload":p,"manifest_sha256":hashlib.sha256(canonicalize_anchor_payload(p)).hexdigest()}
 def backup_to(self,path):
  out=sqlite3.connect(path);self.db.backup(out);out.close()
