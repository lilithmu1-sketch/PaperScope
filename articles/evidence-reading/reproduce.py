"""Re-render the actual figure task offline without modifying original outputs."""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys
ROOT = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(); p.add_argument('--out', type=Path, required=True); a=p.parse_args()
    out=a.out.resolve()
    if out.exists() or out.is_relative_to(ROOT): raise SystemExit('Choose a new directory outside this case.')
    rows=json.loads((ROOT/'checks/artifact-snapshot.json').read_text(encoding='utf-8'))['files']
    def originals():
        assert all(sha(ROOT/'runs/R37'/r['path'])==r['sha256'] for r in rows)
    originals(); out.mkdir(parents=True)
    pdf=ROOT/'materials/paper.pdf'; script=ROOT/'skill/scripts/render_region.py'
    results=[]
    for name in ['overview','figure3']:
        old=json.loads((ROOT/'runs/R37'/name/'provenance.json').read_text(encoding='utf-8'))
        assert sha(pdf)==old['source_pdf_sha256'] and sha(script)==old['script_sha256']
        cmd=[sys.executable,'-B','-X','utf8',str(script),'--pdf',str(pdf),'--page','4','--expected-sha256',old['source_pdf_sha256'],'--out',str(out/name)]
        cmd+=['--overview'] if name=='overview' else ['--rect-normalized','0.065','0.072','0.95','0.55','--scale','5']
        r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=120)
        (out/(name+'-stdout-stderr.txt')).write_text(r.stdout+r.stderr,encoding='utf-8')
        assert r.returncode==0, r.stderr
        matches={f:sha(out/name/f)==entry['sha256'] for f,entry in old['files'].items()}
        assert all(matches.values())
        if name=='overview':
            locator=json.loads((ROOT/'runs/R37/overview/locator-provenance.json').read_text(encoding='utf-8'))
            assert sha(out/name/'locator.png')==locator['locator_sha256']
        results.append({'render':name,'images_byte_identical':matches})
    originals()
    result={'passed':True,'original_artifacts_unchanged':len(rows),'replayed_images':results,'locator_identical':True,'scientific_certification':False}
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__': main()
