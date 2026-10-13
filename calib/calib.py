# Quick BT delay calibration: short 20Hz-20kHz sweep into BT sink, cross-correlate mic vs sink monitor.
# Prints measured delay in ms (or nothing on failure). Uses only numpy.
import numpy as np, wave, subprocess, time, sys, os, tempfile
SR=48000; T=0.5; f1,f2=100,16000; t=np.arange(int(SR*T))/SR; K=T/np.log(f2/f1)
s=np.sin(2*np.pi*f1*K*(np.exp(t/K)-1))*np.hanning(len(t))**0.25*0.25
sig=np.concatenate([np.zeros(SR//4),s,np.zeros(SR//2)])
B,M=sys.argv[1],sys.argv[2]; d=tempfile.mkdtemp()
def w(p,x):
    with wave.open(p,'wb') as f: f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR);f.writeframes((x*32767).astype('<i2').tobytes())
def r(p):
    with wave.open(p) as f: return np.frombuffer(f.readframes(f.getnframes()),'<i2').reshape(-1,f.getnchannels())[:,0]/32768
w(d+'/p.wav',sig); dur=len(sig)/SR+1.0
rec=[subprocess.Popen(['timeout',str(dur),'pw-record']+x+['--rate','48000','--channels','1','--format','s16',d+o],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL) for x,o in [(['--target',M],'/raw.wav'),(['-P','{ stream.capture.sink=true }','--target',B],'/mon.wav')]]
time.sleep(0.5); subprocess.run(['pw-play','--target',B,d+'/p.wav'],stderr=subprocess.DEVNULL)
for p in rec: p.wait()
def lag(x):
    n=1<<int(np.ceil(np.log2(len(x)+len(s)))); cc=np.abs(np.fft.irfft(np.fft.rfft(x,n)*np.conj(np.fft.rfft(s,n)),n)[:len(x)])
    return int(np.argmax(cc)), cc.max()/(np.median(cc)+1e-12)
(lr,qr),(lm,qm)=lag(r(d+'/raw.wav')),lag(r(d+'/mon.wav'))
ms=(lr-lm)/SR*1000
if qr>20 and qm>20 and 30<ms<800: print(round(ms))
