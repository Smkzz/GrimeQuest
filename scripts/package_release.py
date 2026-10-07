"""Package source + evidence with a SHA-256 manifest. Never include credentials."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent
EXCLUDED={'.git','.venv','node_modules','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','walkthrough-frames'}

def selected(path):
    rel=path.relative_to(ROOT)
    if not path.is_file() or any(p in EXCLUDED for p in rel.parts):return False
    if path.name in {'.coverage','.DS_Store','BUILD_MANIFEST.json'}:return False
    if path.name.startswith('.env') and path.name!='.env.example':return False
    if path.suffix in {'.pyc','.ttf','.otf','.woff','.woff2'}:return False
    return True

def main():
    files=sorted(p for p in ROOT.rglob('*') if selected(p))
    records=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
    aggregate=hashlib.sha256('\n'.join(r['path']+' '+r['sha256'] for r in records).encode()).hexdigest()
    manifest={'project':'GrimeQuest','version':'0.1.0','source_date':'2026-10-06','qualification':'automated app/protocol qualified; real vision accuracy, target-phone behavior and physical cleaning remain unverified',
              'manifest_algorithm':'SHA-256; aggregate hashes ordered path + space + file digest, newline-separated',
              'aggregate_sha256':aggregate,'files':records}
    (ROOT/'BUILD_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    archive=OUT/'GrimeQuest-v0.1.0.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in [*files,ROOT/'BUILD_MANIFEST.json']:
            info=zipfile.ZipInfo('grimequest/'+str(p.relative_to(ROOT)),date_time=(2026,10,6,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,p.read_bytes())
    for source,name in [('preview.html','GrimeQuest-preview.html'),('docs/TEST_REPORT.md','GrimeQuest-test-report.md'),('evidence/home-desktop.png','GrimeQuest-desktop.png'),('evidence/home-mobile.png','GrimeQuest-mobile.png'),('evidence/interface-walkthrough.mp4','GrimeQuest-interface-walkthrough.mp4')]:
        source_path=ROOT/source
        if source_path.is_file():
            shutil.copy2(source_path,OUT/name)
    # Read back every archive member against its manifest, not merely the ZIP header.
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for record in records:
            assert hashlib.sha256(z.read('grimequest/'+record['path'])).hexdigest()==record['sha256']
    checksum=hashlib.sha256(archive.read_bytes()).hexdigest()
    (OUT/'GrimeQuest-SHA256.txt').write_text(checksum+'  '+archive.name+'\n'+aggregate+'  manifest aggregate (see BUILD_MANIFEST.json)\n')
    print(json.dumps({'archive':str(archive),'archive_bytes':archive.stat().st_size,'file_count':len(records)+1,'zip_sha256':checksum,'manifest_aggregate':aggregate},indent=2))

if __name__=='__main__':main()
