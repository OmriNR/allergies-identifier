import React, {useState, useRef, useEffect } from 'react'
import { Camera, X, ScanLine, Keyboard } from 'lucide-react'
import { Button } from './ui/button'
import { Input } from './ui/input'

interface BarcodeScannerProps {
    onScan: (barcode: string) => void
}

export default function BarcodeScanner( { onScan }: BarcodeScannerProps) {
    const [stream, setStream] = useState<MediaStream | null>(null);
    const [error, setError] = useState<string>("")
    const [manualMode, setManualMode] = useState<boolean>(false)
    const [manualValue, setManualValue] = useState<string>("")
    const [cameraValue, setCameraValue] = useState<string>("")
    const videoRef = useRef<HTMLVideoElement>(null)

    const startCamera = async () => {
        setError("")
        try {
            const mediaStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: "environment" }
            });
            setStream(mediaStream)
            setManualMode(false)
        }
        catch {
            setError("Camera access denied. You can enter barcode manually instead.")
            setManualMode(true);
        }
    };

    const stopCamera = () => {
        if (stream) {
            stream.getTracks().forEach(t => t.stop());
        }
        setStream(null)
    }

    useEffect(() => {

        if (stream && videoRef.current) {
            videoRef.current.srcObject = stream;
        }

        return () => {
            if (stream) {
                stream.getTracks().forEach(t => t.stop());
            }
        };

    }, [stream])

    const handleManualSubmit = (e : React.SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();
        
        if (manualValue.trim()) {
            onScan(manualValue.trim())
        }
    };

    return (
        <div className='w-full'>
            {!stream && !manualMode && (
                <div className='flex flex-col items-center gap-4 py-8'>
                    <button onClick={startCamera} className="group relative flex h-40 w-40 items-center justify-center rounded-full bg-primary text-primary-foreground transition-transform hover:scale-105 active:scale-95">
                        <Camera className='h-16 w-16' />
                        <span className='absolute -bottom-9 text-sm font-medium text-foreground'>Scan barcode</span>
                    </button>
                    <button onClick={() => setManualMode(true)} className="mt-6 inline-flex items-center gap-2 text-sm text-muted-foreground underline-offset-4 hover:underline">
                        <Keyboard className='h-4 w-4' /> Enter manually
                    </button>
                </div>
            )}

            {stream && (
                <div className='relative overflow-hidden rounded-2xl bg-black'>
                    <video ref={videoRef} autoPlay playsInline muted className='h-72 w-full object-cover'/>

                    <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                        <div className="relative h-40 w-64 rounded-xl border-2 border-white/80 shadow-[0_0_0_1000px_rgba(0,0,0,0.4)]">
                            <ScanLine className="absolute left-1/2 top-1/2 h-10 w-10 -translate-x-1/2 -translate-y-1/2 text-white/90 animate-pulse" />
                        </div>
                    </div>

                    <button onClick={stopCamera} className="absolute right-3 top-3 rounded-full bg-black/40 p-1.5 text-white">
                        <X className='h-4 w-4' />
                    </button>
                </div>
            )}

            {stream && (
                <form className='mt-3 flex gap-2' onSubmit={(e: React.SubmitEvent<HTMLFormElement>) => {
                    e.preventDefault();

                    if (cameraValue.trim()) {
                        stopCamera();
                        onScan(cameraValue.trim())
                    }
                }}>
                    <Input 
                        placeholder='Scanned barcode' 
                        value={cameraValue}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                            setCameraValue(e.target.value)
                        }}
                        inputMode='numeric'
                        autoFocus
                    />

                    <Button type='submit' disabled={!cameraValue.trim()}>Check</Button>        
                </form>
            )}

            {manualMode && (
                <form onSubmit={handleManualSubmit} className='flex flex-col gap-3 py-4'>
                    <Input 
                        autoFocus 
                        placeholder='e.g 5901234123457' 
                        value={manualValue}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                            setManualValue(e.target.value)
                        }} 
                        inputMode='numeric'
                    />

                    <div className="flex gap-2">
                        <Button type="submit" disabled={!manualValue.trim()} className="flex-1">
                            Check product
                        </Button>
                        <Button type="button" variant="outline" onClick={() => setManualMode(false)}>
                            Cancel
                        </Button>
                    </div>
                </form>
            )}

            {error && <p className='mt-3 text-center text-sm text-destructive'>{error}</p>}
        </div>
    )
}
