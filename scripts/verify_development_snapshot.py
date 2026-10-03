"""Check immutable published development evidence without rerunning/writing it."""
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def verify(folder):
    manifest=json.loads((ROOT/folder/'manifest.json').read_text())
    for name,expected in manifest['source_hashes'].items():
        actual=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        assert actual==expected,('source changed since study freeze',name)
    for name,expected in manifest['output_hashes'].items():
        path=ROOT/name
        if not path.exists():path=ROOT/folder/name
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,name
    print('Published snapshot hashes verified:',folder)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);verify(p.parse_args().folder)
