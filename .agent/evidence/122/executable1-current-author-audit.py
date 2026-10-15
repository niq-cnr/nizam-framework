"""Apply the same independent frozen audit predicates to the author's raw run."""
from pathlib import Path
path=Path(__file__).with_name('executable1-current-audit.py')
code=path.read_text()
old='controls3-executable-review1-result.json';new='controls3-runtime2-result.json'
assert code.count(old)==1
exec(compile(code.replace(old,new),str(path),'exec'),{'__file__':str(path),'__name__':'__main__'})
