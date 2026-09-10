"""AQ canonical JSON V1; no serializer defaults define identity."""
from __future__ import annotations
import hashlib,json,math,unicodedata
from datetime import date,datetime,timezone
from decimal import Decimal,InvalidOperation
RESEARCH_CANONICAL_V1="AQ_RESEARCH_SPEC_CANONICAL_V1"; ANCHOR_CANONICAL_V1="AQ_LEDGER_ANCHOR_CANONICAL_V1"
class CanonicalizationError(ValueError): pass
def parse_json_strict(text):
 def pairs(items):
  d={}
  for k,v in items:
   if k in d: raise CanonicalizationError("duplicate key")
   d[k]=v
  return d
 def bad(x): raise CanonicalizationError("non-finite number")
 try:return json.loads(text,object_pairs_hook=pairs,parse_constant=bad)
 except (ValueError,json.JSONDecodeError) as e:raise CanonicalizationError(str(e))
def _decimal(v):
 try:d=Decimal(str(v))
 except InvalidOperation as e:raise CanonicalizationError("invalid decimal") from e
 if not d.is_finite():raise CanonicalizationError("non-finite number")
 if not d:return "0"
 s=format(d.normalize(),"f");return s.rstrip("0").rstrip(".") if "." in s else s
def _norm(v,dec,f=None):
 if isinstance(v,dict):return {str(k):_norm(x,dec,str(k)) for k,x in v.items()}
 if isinstance(v,list):return [_norm(x,dec,f) for x in v]
 if isinstance(v,datetime):
  if v.tzinfo is None or v.utcoffset() is None:raise CanonicalizationError("naive datetime")
  return v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
 if isinstance(v,date):return v.isoformat()
 if isinstance(v,float) and not math.isfinite(v):raise CanonicalizationError("non-finite number")
 if f in dec:return _decimal(v)
 if isinstance(v,str):
  if any(0xd800<=ord(x)<=0xdfff for x in v):raise CanonicalizationError("lone surrogate")
  return unicodedata.normalize("NFC",v)
 return v
def _emit(v):
 s=json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)
 s=s.replace("\\b","\\u0008").replace("\\f","\\u000c").replace("\\n","\\u000a").replace("\\r","\\u000d").replace("\\t","\\u0009")
 return "".join(f"\\u{ord(c):04x}" if ord(c)<=31 else c for c in s).encode()
def canonicalize_research_spec(spec,*,decimal_fields=(),version=RESEARCH_CANONICAL_V1):
 if version!=RESEARCH_CANONICAL_V1:raise CanonicalizationError("unknown canonicalization version")
 if set(spec)&{"trial_id","idempotency_key","request_id","registered_at","registration_actor","execution_id","result","performance_metrics"}:raise CanonicalizationError("registration metadata")
 return _emit({"canonicalization_version":version,"research_spec":_norm(spec,set(decimal_fields))})
def hash_research_spec(spec,**kw):
 b=canonicalize_research_spec(spec,**kw);return b,hashlib.sha256(b).hexdigest()
def canonicalize_anchor_payload(payload):
 if payload.get("canonicalization_version",ANCHOR_CANONICAL_V1)!=ANCHOR_CANONICAL_V1:raise CanonicalizationError("unknown anchor version")
 return _emit({"canonicalization_version":ANCHOR_CANONICAL_V1,"payload":_norm(payload,set())})
