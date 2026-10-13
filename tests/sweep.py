# Dev-only benchmark: plays N log sweeps on the speaker. Set MIC=<source name>.
import os
import numpy as np, wave, subprocess, time, sys, json
SR=48000; T=2.0; f1,f2=20,20000; N=int(sys.argv[1]) if len(sys.argv)>1 else 5
t=np.arange(int(SR*T))/SR; K=T/np.log(f2/f1)
s=np.sin(2*np.pi*f1*K*(np.exp(t/K)-1)); fade=int(0.01*SR); s[:fade]*=np.linspace(0,1,fade); s[-fade:]*=np.linspace(1,0,fade)
inv=s[::-1]*np.exp(-t/K)  # Farina inverse filter
gap=np.zeros(int(SR*1.2)); sig=np.concatenate([gap]+[np.concatenate([s*0.5,gap]) for _ in range(N)])
def w(p,x):
    with wave.open(p,'wb') as f: f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR);f.writeframes((x*32767).astype('<i2').tobytes())
def r(p):
    with wave.open(p) as f: return np.frombuffer(f.readframes(f.getnframes()),'<i2').reshape(-1,f.getnchannels())[:,0]/32768
w('sw_play.wav',sig)
M=os.environ.get('MIC','YOUR_MIC_SOURCE'); B=subprocess.check_output("pactl list short sinks|awk '/bluez_output/{print $2;exit}'",shell=True,text=True).strip()
dur=len(sig)/SR+1.5
recs=[subprocess.Popen(["env","PIPEWIRE_LATENCY=256/48000",'timeout',str(dur),'pw-record']+x+['--rate','48000','--channels','1','--format','s16',o]) for x,o in [(['--target',M],'sw_raw.wav'),(['--target','echo_mic'],'sw_ec.wav'),(['-P','{ stream.capture.sink=true }','--target',B],'sw_mon.wav')]]
time.sleep(0.6); subprocess.run(['pw-play','--target','echo_softvol','sw_play.wav'])
for p in recs: p.wait()
raw,ec,mon=r('sw_raw.wav'),r('sw_ec.wav'),r('sw_mon.wav')
def ir(x):
    n=1<<int(np.ceil(np.log2(len(x)+len(inv)))); return np.fft.irfft(np.fft.rfft(x,n)*np.fft.rfft(inv,n),n)
def peaks(h):
    # find N strongest separated peaks
    a=np.abs(h).copy(); out=[]
    for _ in range(N):
        i=int(np.argmax(a)); out.append(i); a[max(0,i-SR):i+SR]=0
    return sorted(out)
hr,hm=ir(raw),ir(mon); pr,pm=peaks(hr),peaks(hm)
d=[(a-b)/SR*1000 for a,b in zip(pr,pm)]
bands=[31,63,125,250,500,1000,2000,4000,8000,16000]; resp=[]
for p in pr:
    seg=hr[p-int(0.005*SR):p+int(0.3*SR)]; F=np.abs(np.fft.rfft(seg,1<<16)); fr=np.fft.rfftfreq(1<<16,1/SR)
    resp.append([20*np.log10(np.sqrt(np.mean(F[(fr>=b/np.sqrt(2))&(fr<b*np.sqrt(2))]**2))+1e-12) for b in bands])
resp=np.array(resp); resp-=resp[:,5:6]  # relative to 1 kHz
db=lambda x:20*np.log10(np.sqrt(np.mean(x**2))+1e-9)
print(json.dumps({'delays_ms':d,'mean':float(np.mean(d)),'std':float(np.std(d)),'bands':bands,'resp_mean':resp.mean(0).round(1).tolist(),'resp_std':resp.std(0).round(1).tolist(),
 'raw_db':db(raw),'ec_db':db(ec),'snr_peak':float(np.abs(hr).max()/np.median(np.abs(hr)))}))
