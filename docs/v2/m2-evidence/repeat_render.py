"""Counterbalanced fresh-process follow-up for an explicitly selected timing cell."""
import argparse, hashlib, json, statistics, subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--baseline-python',required=True)
p.add_argument('--candidate-python',required=True)
p.add_argument('--driver',type=Path,required=True)
p.add_argument('--workload-script',type=Path,required=True)
p.add_argument('--workload',required=True)
p.add_argument('--aa',required=True)
p.add_argument('--trials',type=int,default=9)
p.add_argument('--frames',default='120')
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
r={'protocol':'fresh processes; baseline/candidate order alternates each pair; fixed trial count selected before this repeat',
   'frames_per_trial':int(a.frames),'trial_pairs':a.trials,
   'workload_sha256':hashlib.sha256(a.workload_script.read_bytes()).hexdigest(),
   'workload':a.workload,'aa':int(a.aa),'trials':[]}
samples={'baseline':[],'candidate':[]}
for i in range(a.trials):
    order=('baseline','candidate') if i%2==0 else ('candidate','baseline')
    for label in order:
        python=a.baseline_python if label=='baseline' else a.candidate_python
        completed=subprocess.run([python,'-I','-B',str(a.driver.resolve()),'--worker','render',str(a.workload_script.resolve()),a.workload,a.aa,a.frames],cwd='/tmp',capture_output=True,text=True,check=True)
        result=json.loads(completed.stdout)
        samples[label].append(result)
        r['trials'].append({'pair':i,'label':label,'result':result})
        a.output.write_text(json.dumps(r,indent=2)+'\n')
r['summary']={label:{m:statistics.median(s[m] for s in values) for m in ('median_ms','p95_ms','cold_frame_ms','process_peak_rss_kib')} for label,values in samples.items()}
r['gate']=all(r['summary']['candidate'][m]<=1.1*r['summary']['baseline'][m] for m in ('median_ms','p95_ms'))
a.output.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'summary':r['summary'],'gate':r['gate']}),flush=True)
