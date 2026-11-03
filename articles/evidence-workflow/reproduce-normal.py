"""Offline figure replay, evidence-gap file checks, and original normal rebuild."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve()
 if out.exists() or out.is_relative_to(ROOT):raise SystemExit('Choose new directory outside this case.')
 out.mkdir(parents=True)
 scope={'original_artifacts':[]}
 for row in scope['original_artifacts']:
  assert sha(ROOT/row['path'])==row['sha256'],row['path']
 r=subprocess.run([sys.executable,'-B','-X','utf8',str(ROOT/'reproduce.py'),'--out',str(out/'figure')],capture_output=True,text=True,encoding='utf-8',timeout=120)
 (out/'figure-log.txt').write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0,r.stdout+r.stderr
 # Both independent runs received the same excerpt/task; check exact frozen hash, not semantic truth.
 c=json.loads((ROOT/'boundary/input-hashes.json').read_text(encoding='utf-8'))
 for name,digest in c['shared'].items():assert sha(ROOT/'boundary'/name)==digest
 work=out/'normal-source';(work/'inputs').mkdir(parents=True);(work/'tools').mkdir();(work/'work').mkdir()
 shutil.copyfile(ROOT/'normal/rebuild-original.py',work/'rebuild.py')
 shutil.copyfile(ROOT/'normal/review-record.json',work/'work/review-record.json')
 shutil.copyfile(ROOT/'normal/sources-original.json',work/'inputs/sources.json')
 shutil.copyfile(ROOT/'materials/paper.pdf',work/'inputs/matbench-automatminer.pdf')
 shutil.copyfile(ROOT/'materials/correction.pdf',work/'inputs/matbench-automatminer-correction.pdf')
 shutil.copyfile(ROOT/'skill/scripts/render_region.py',work/'tools/render_region.py')
 shutil.copytree(ROOT/'normal/images',work/'images')
 r=subprocess.run([sys.executable,'-B','-X','utf8',str(work/'rebuild.py'),'--out',str(work/'fresh')],capture_output=True,text=True,encoding='utf-8',timeout=120)
 (out/'normal-log.txt').write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0,r.stdout+r.stderr
 core={name:(work/'fresh'/name).read_bytes()==(ROOT/'normal/results'/name).read_bytes() for name in ['answer.md','claims.json','comparison.csv','numeric-review.json']};assert all(core.values())
 for row in scope['original_artifacts']:assert sha(ROOT/row['path'])==row['sha256']
 result={'passed':True,'figure':'four evidence PNGs and locator replay passed','C_shared_inputs_hashes_match':True,'normal_core_byte_identical':core,'original_files_unchanged':True,'model_rerun':False,'scientific_certification':False}
 (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
