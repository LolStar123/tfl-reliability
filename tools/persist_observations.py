"""Commit public history to its own branch without changing the source checkout."""
import subprocess

def git(*args, input=None, check=True):
    return subprocess.run(['git', *args], input=input, capture_output=True, text=True, check=check)

def main():
    parent=git('rev-parse','--verify','refs/remotes/origin/observations',check=False)
    blob=git('hash-object','-w','observations/history.json').stdout.strip()
    tree=git('mktree',input=f'100644 blob {blob}\thistory.json\n').stdout.strip()
    args=['-c','user.name=github-actions[bot]','-c','user.email=41898282+github-actions[bot]@users.noreply.github.com','commit-tree',tree]
    if parent.returncode==0:args.extend(['-p',parent.stdout.strip()])
    commit=git(*args,input='Collect real TfL network observations\n').stdout.strip()
    git('push','origin',commit+':refs/heads/observations')

if __name__=='__main__':main()
