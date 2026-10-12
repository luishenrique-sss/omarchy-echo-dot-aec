import os
import numpy as np, wave, subprocess, time, sys
SR=48000; kind=sys.argv[1] if len(sys.argv)>1 else 'chirp'
t=np.arange(int(SR*0.4))/SR
if kind=='chirp':
    c=np.sin(2*np.pi*(300*t+(4000-300)/(2*0.4)*t**2))*np.hanning(len(t))
    sig=np.concatenate([np.zeros(SR//2),c,np.zeros(SR//2),c,np.zeros(SR//2)])*0.6
else:
    rng=np.random.default_rng(1); n=rng.standard_normal(SR*3)
    f=np.fft.rfft(n); fr=np.fft.rfftfreq(len(n),1/SR); f/=np.maximum(fr,50)**0.5; n=np.fft.irfft(f)
    env=0.6+0.4*np.sin(2*np.pi*2*np.arange(len(n))/SR)
    sig=np.concatenate([np.zeros(SR//2),n/np.abs(n).max()*env*0.5,np.zeros(SR//2)])
def w(p,x):
    with wave.open(p,'wb') as f: f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR);f.writeframes((x*32767).astype('<i2').tobytes())
def r(p):
    with wave.open(p) as f: return np.frombuffer(f.readframes(f.getnframes()),'<i2').reshape(-1,f.getnchannels())[:,0]/32768
w('play.wav',sig)
M=os.environ.get('MIC','SEU_MICROFONE')
dur=len(sig)/SR+1.0
recs=[subprocess.Popen(["env","PIPEWIRE_LATENCY=256/48000",'timeout',str(dur+0.6),'pw-record']+x+['--rate','48000','--channels','1','--format','s16',o]) for x,o in [(['--target',M],'raw.wav'),(['--target',os.environ.get('SRC','echo_mic')],'ec.wav'),(['-P','{ stream.capture.sink=true }','--target',os.environ.get('BT_SINK','bluez_output.AA_BB_CC_DD_EE_FF.1')],'mon.wav')]]
time.sleep(0.6); subprocess.run(['pw-play','--target',os.environ.get('SNK','echo_softvol'),'play.wav'])
for p in recs: p.wait()
raw,ec,mon=r('raw.wav'),r('ec.wav'),r('mon.wav')
def lag(x):
    n=1<<int(np.ceil(np.log2(len(x)+len(sig))))
    cc=np.fft.irfft(np.fft.rfft(x,n)*np.conj(np.fft.rfft(sig,n)),n)[:len(x)]
    return int(np.argmax(np.abs(cc)))
L=lag(raw); a=L+SR//2; b=a+len(sig)-SR
db=lambda x:20*np.log10(np.sqrt(np.mean(x**2))+1e-9)
rawE,ecE=db(raw[a:b]),db(ec[a:min(b,len(ec))]); noise=db(raw[:max(L//2,1000)])
lat=(L-lag(mon))/SR*1000
att=rawE-ecE; cls='ausente' if ecE<noise+3 else ('leve' if att>25 else 'presente')
print(f"{kind}: total={L/SR*1000:.0f}ms lat_rel={lat:.0f}ms raw={rawE:.1f}dB ec={ecE:.1f}dB ruido={noise:.1f}dB atenuacao={att:.1f}dB eco={cls}")
for nm,x in [('raw',raw),('ec',ec),('mon',mon)]:
    n=1<<int(np.ceil(np.log2(len(x)+len(sig))));cc=np.abs(np.fft.irfft(np.fft.rfft(x,n)*np.conj(np.fft.rfft(sig,n)),n)[:len(x)])
    print(nm,'lag_ms',np.argmax(cc)/SR*1000,'peak/median',round(cc.max()/np.median(cc),1))
