import { useState, useEffect, useRef } from 'react';

const useVoiceRecognition = () => {
  const [isListening, setIsListening] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [error, setError] = useState(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    let stream = null;
    
    
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
      }
    };
  }, [mediaRecorder]);

  const startListening = async () => {
    setError(null);
    audioChunksRef.current = [];
    setAudioBlob(null);
    
    try {
      console.log("마이크 액세스 요청 중...");
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      
      console.log("마이크 액세스 성공, 레코더 생성 중...");
      
      
      const recorder = new MediaRecorder(stream, { 
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 128000
      });
      setMediaRecorder(recorder);
      
      
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          console.log(`오디오 청크 추가: ${e.data.size} bytes`);
          audioChunksRef.current.push(e.data);
        }
      };
      
      
      recorder.onstop = () => {
        console.log(`녹음 완료: ${audioChunksRef.current.length} 청크`);
        if (audioChunksRef.current.length > 0) {
          const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          console.log(`생성된 오디오 블롭 크기: ${blob.size} bytes`);
          setAudioBlob(blob);
        } else {
          console.error("음성 데이터가 없습니다.");
          setError("음성이 감지되지 않았습니다. 다시 시도해주세요.");
        }
        
        
        stream.getTracks().forEach(track => track.stop());
      };
      
      
      recorder.onerror = (event) => {
        console.error("녹음 중 오류:", event.error);
        setError(`녹음 중 오류가 발생했습니다: ${event.error}`);
      };
      
      
      recorder.start(100); 
      console.log("녹음 시작됨");
      setIsListening(true);
      
    } catch (err) {
      console.error('마이크 접근 오류:', err);
      setError('마이크 접근에 실패했습니다. 마이크 권한을 확인해주세요.');
    }
  };

  const stopListening = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      console.log("녹음 중지 요청됨");
      mediaRecorder.stop();
    }
    setIsListening(false);
  };

  const resetAudio = () => {
    console.log("오디오 데이터 초기화");
    setAudioBlob(null);
    audioChunksRef.current = [];
  };

  return {
    isListening,
    audioBlob,
    error,
    startListening,
    stopListening,
    resetAudio
  };
};

export default useVoiceRecognition;
