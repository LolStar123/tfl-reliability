"""Commit public history to its own branch without changing the source checkout."""
import subprocess
from pathlib import Path

def git(*args, input=None, check=True):
    text = not isinstance(input, (bytes, bytearray))
    return subprocess.run(['git', *args], input=input, capture_output=True, text=text, check=check)

def main():
    parent=git('rev-parse','--verify','refs/remotes/origin/observations',check=False)
    entries=[]
    sources = {
        'history.json': Path('observations/history.json'),
        'events.json': Path('observations/events.json'),
        'feed.json': Path('examples/portfolio/data/events.json'),
    }
    for name,path in sources.items():
        if path.exists():
            blob=git('hash-object','-w',str(path)).stdout.strip()
            entries.append(f'100644 blob {blob}\t{name}\0')
    tree=git('mktree','-z',input=''.join(entries).encode()).stdout.decode().strip()
    args=['-c','user.name=github-actions[bot]','-c','user.email=41898282+github-actions[bot]@users.noreply.github.com','commit-tree',tree]
    if parent.returncode==0:args.extend(['-p',parent.stdout.strip()])
    commit=git(*args,input='Collect real TfL network observations\n').stdout.strip()
    git('push','origin',commit+':refs/heads/observations')
    git('update-ref','refs/remotes/origin/observations',commit)

if __name__=='__main__':main()
