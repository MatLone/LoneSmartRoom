"""Generate only simulated reports and a static review; external operations denied."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def deny(event,args):
    if event.startswith(('socket.','winreg.')) or event in (
        'subprocess.Popen','os.system','os.startfile','os.startfile/2',
        'ctypes.dlopen','ctypes.call_function','os.exec','os.posix_spawn'):
        raise RuntimeError('External operations forbidden in simulated review')


def main():
    sys.addaudithook(deny)
    from diagnostics.scenarios import mixed_review
    from diagnostics.presentation import present,render_html
    out=ROOT/'docs/diagnostics-adapters-2026-10-26'
    out.mkdir(parents=True,exist_ok=True)
    report=mixed_review()
    for name,data in (('SIMULATED-report.json',report),('SIMULATED-view.json',present(report))):
        (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'review.html').write_text(render_html(report),encoding='utf-8',newline='\n')
    print('PASS: eight simulated read-only diagnostic cards; no probes, repair or installed app.')


if __name__=='__main__':main()
