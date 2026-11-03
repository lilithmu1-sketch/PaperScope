"""Offline rebuild from raw PDFs and authored work record, never copies final views."""
from pathlib import Path
import argparse,json,hashlib,subprocess,sys,re,csv,io
from decimal import Decimal,ROUND_HALF_UP
from datetime import datetime,timezone
from pypdf import PdfReader
from PIL import Image
ROOT=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(t): return re.sub(r'\s+',' ',t).strip()
def dump(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 a=argparse.ArgumentParser(); a.add_argument('--out',required=True); args=a.parse_args()
 out=Path(args.out).resolve(); out.mkdir(parents=True,exist_ok=False)
 checks={'utc':datetime.now(timezone.utc).isoformat(),'output':str(out),'review_type':'offline engineering replay; not independent scientific verification','checks':[]}
 sources=json.loads((ROOT/'inputs/sources.json').read_text(encoding='utf-8'))['sources']
 for s in sources:
  actual=sha(ROOT/'inputs'/s['file']); assert actual==s['sha256'],s['file']; checks['checks'].append({'source':s['file'],'sha256':actual,'status':'match registered input'})
 pages={}
 for source,file in [('main','matbench-automatminer.pdf'),('correction','matbench-automatminer-correction.pdf')]:
  reader=PdfReader(ROOT/'inputs'/file)
  pages[source]=[(p.extract_text() or '').replace('\r\n','\n').replace('\r','\n') for p in reader.pages]
 dump(out/'extracted-pages.json',pages)
 record=json.loads((ROOT/'work/review-record.json').read_text(encoding='utf-8'))
 anchors=[]
 for c in record['claims']:
  if not c['quote']: continue
  text=norm(pages[c['source']][c['physical_page']-1]); quote=norm(c['quote']); start=text.find(quote)
  assert start>=0,(c['id'],'quote not found')
  c['anchor_id']=c['id']; anchors.append({'id':c['id'],'source':c['source'],'physical_page':c['physical_page'],'normalization':'whitespace collapsed; offsets refer to normalized page text','start':start,'end':start+len(quote),'quote':quote})
 dump(out/'anchors.json',anchors)
 checks['checks'].append({'quote_anchors':len(anchors),'status':'all exact after whitespace normalization'})
 # These are original visual transcriptions, not guessed from extracted text.
 rd=record['readings']; am=Decimal(rd['automatminer']); rf=Decimal(rd['rf'])
 delta=am-rf; improvement=(rf-am)/rf*100; reverse=(rf-am)/am*100
 fmt=lambda x: str(x.quantize(Decimal('.01'),rounding=ROUND_HALF_UP))
 numbers={'scope':'Main PDF physical p4 Fig3; values visually checked against retained context and detail, label checked against correction p1. No per-fold values or significance test.','readings':[dict(id='N01',model='Automatminer',value=str(am),**{k:v for k,v in rd.items() if k not in ['automatminer','rf']}),dict(id='N02',model='composition RF',value=str(rf),**{k:v for k,v in rd.items() if k not in ['automatminer','rf']})],'calculations':[{'id':'N03','inputs':{'autom':str(am),'rf':str(rf)},'signed_difference_formula':'autom-rf','signed_difference_MPa':str(delta),'reduction_MPa':str(-delta),'relative_reduction_formula':'(rf-autom)/rf*100','direction':'positive reduction means Automatminer has lower MAE','denominator':'RF 104 MPa','raw_percent':str(improvement),'rounded_percent':fmt(improvement),'rounding':'Decimal ROUND_HALF_UP 2 decimal places; input precision limited to published rounded labels','reverse_denominator_autom_percent':fmt(reverse)}],'unit_review':{'id':'N04','source':'correction','physical_page':1,'quote':'Yield Strength (GPa) / Yield Strength (MPa)','result':'label corrected to MPa; supplied main Fig3 already MPa; no multiplying these readings by 1000'},'other_numbers':[{'metric':'steel sample count','value':312,'source':'main','physical_page':3,'location':'Table1 final row','unit':'samples','scope':'text extraction; no local sample count audit'},{'metric':'outer CV folds','value':5,'source':'main','physical_page':7,'location':'Evaluation methods','unit':'folds','scope':'randomized KFold, seed 18012019; not group CV'},{'metric':'software version','value':'Automatminer v1.0.3.20191111 / TPOT v.10.1','source':'main','physical_page':8,'location':'Machine learning pipelines','scope':'historical experiment only'},{'metric':'Express search limit','value':24,'unit':'hours per outer fold','source':'main','physical_page':8,'location':'Methods TPOT paragraph','scope':'100 individuals/generation; 20 min per pipeline; 10-way parallelism'}]}
 assert delta==Decimal('-8.8') and fmt(improvement)=='8.46'
 dump(out/'claims.json',{'claims':record['claims'],'numeric_claims':['N01','N02','N03','N04'],'numeric_details':'numeric-review.json','source_registry':'../inputs/sources.json','scope':'facts versus model-authored proposals/unknowns are typed; numeric graph values are visual readings'})
 dump(out/'numeric-review.json',numbers)
 with (out/'comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['维度','论文条件','本地条件','判断与准备']);w.writerows(record['comparison'])
 (out/'answer.md').write_text('# 钢屈服强度预测起点：PaperScope研究建议\n\n'+'\n\n'.join('## '+t+'\n\n'+body for t,body in record['sections'])+'\n',encoding='utf-8')
 # Re-render actual original pages and compare decoded pixels to original evidence.
 for name,source,page,rect in [('p4-overview','main',4,None),('correction','correction',1,None),('steel-detail','main',4,[.19,.075,.37,.31])]:
  pdf='matbench-automatminer.pdf' if source=='main' else 'matbench-automatminer-correction.pdf'
  cmd=[sys.executable,'-B','-X','utf8',str(ROOT/'tools/render_region.py'),'--pdf',str(ROOT/'inputs'/pdf),'--page',str(page),'--out',str(out/'images'/name)]
  cmd+=['--overview'] if rect is None else ['--rect-normalized',*map(str,rect),'--scale','5']
  run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=110)
  checks['checks'].append({'render':name,'command':cmd,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
  assert run.returncode==0
  for filename in ['context.png','region.png']:
   with Image.open(ROOT/'images'/name/filename) as original,Image.open(out/'images'/name/filename) as replay:
    assert original.size==replay.size and original.tobytes()==replay.tobytes()
   checks['checks'].append({'pixel_comparison':name+'/'+filename,'status':'identical'})
 checks['checks'].append({'calculation':'(104-95.2)/104*100','result':fmt(improvement),'status':'recomputed'})
 checks['core_sha256']={n:sha(out/n) for n in ['answer.md','claims.json','comparison.csv','numeric-review.json']}
 dump(out/'checks.json',checks)
 print(json.dumps({'status':'passed','out':str(out),'anchors':len(anchors),'core_sha256':checks['core_sha256']},ensure_ascii=False))
if __name__=='__main__': main()
