import React, { useEffect, useState, useRef } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { FaMicrophone, FaTimes } from 'react-icons/fa';
import useVoiceRecognition from '../hooks/useVoiceRecognition';
import { analyzeOrder, respondToClarification } from '../services/api';

const ModalOverlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
`;

const ModalContent = styled(motion.div)`
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: white;
  padding: 2rem;
`;

const VoiceWaveContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  width: 250px;
  height: 250px;
  margin-bottom: 2rem;
  position: relative;
`;

const WaveCircle = styled(motion.div)`
  position: absolute;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
`;

const MicrophoneButton = styled(motion.button)`
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background-color: var(--accent-color);
  border: none;
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  z-index: 10;
  font-size: 2.5rem;
  box-shadow: 0 0 20px rgba(255, 255, 255, 0.2);
  
  &:hover {
    background-color: #44a86b;
  }
  
  &:focus {
    outline: none;
  }
`;

const CloseButton = styled(motion.button)`
  position: absolute;
  top: 2rem;
  right: 2rem;
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  z-index: 20;
  
  &:hover {
    color: var(--accent-color);
  }
  
  &:focus {
    outline: none;
  }
`;

const StatusText = styled(motion.p)`
  font-size: 1.5rem;
  margin-top: 1rem;
  color: white;
  text-align: center;
  max-width: 80%;
`;

const ResponseText = styled(motion.div)`
  font-size: 1.8rem;
  margin-top: 2rem;
  color: white;
  text-align: center;
  max-width: 80%;
  line-height: 1.5;
`;

/*
const ClarificationContainer = styled(motion.div)`
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 2rem;
  width: 90%;
`;

const ClarificationItem = styled.div`
  background-color: rgba(255, 255, 255, 0.1);
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  font-size: 1.5rem;
  width: 100%;
  text-align: center;
`;

const ClarificationInput = styled.input`
  width: 100%;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  background-color: rgba(0, 0, 0, 0.3);
  color: white;
  font-size: 1.2rem;
  margin-top: 1rem;
  text-align: center;
  
  &:focus {
    outline: none;
    border-color: var(--accent-color);
  }
`;

const ButtonContainer = styled.div`
  display: flex;
  justify-content: center;
  margin-top: 1rem;
  gap: 1rem;
`;

const ClarificationButton = styled(motion.button)`
  padding: 0.8rem 1.5rem;
  border-radius: 8px;
  border: none;
  background-color: var(--accent-color);
  color: white;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  &:hover {
    background-color: #44a86b;
  }
  
  &:focus {
    outline: none;
  }
`;
*/

const InstructionText = styled.p`
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 1rem;
  margin-bottom: 2rem;
  text-align: center;
`;

const VoiceModal = ({ isOpen, onClose, onOrderComplete }) => {
  const { isListening, audioBlob, error, startListening, stopListening, resetAudio } = useVoiceRecognition();
  const [status, setStatus] = useState('대화 시작하려면 마이크를 누르세요');
  const [response, setResponse] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [needsClarification, setNeedsClarification] = useState(false);
  const [clarificationItem, setClarificationItem] = useState('');
  const [clarificationMode, setClarificationMode] = useState(false);
  const processedAudioRef = useRef(false);
  const [currentOrder, setCurrentOrder] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setStatus('주문을 시작하려면 마이크 버튼을 누르세요');
      setResponse(null);
      setHasError(false);
      setClarificationMode(false);
      setNeedsClarification(false);
      
      setCurrentOrder(null);
      processedAudioRef.current = false;
      console.log('새로운 주문 세션이 시작되었습니다.');
    }
  }, [isOpen]);

  useEffect(() => {
    if (error) {
      setStatus(error);
      setHasError(true);
      setIsLoading(false);
    }
  }, [error]);

  useEffect(() => {
    const processAudio = async () => {
      
      if (!isListening && audioBlob && audioBlob.size > 0 && !processedAudioRef.current) {
        processedAudioRef.current = true; 
        setIsLoading(true);
        setHasError(false);
        
        try {
          console.log(`서버로 오디오 파일 전송 시작 (${audioBlob.size} bytes)`);
          
          
          if (clarificationMode) {
            setStatus('추가 정보 처리 중...');
            const result = await respondToClarification(audioBlob);
            console.log('명확화 응답 결과:', result);
            
            if (result.status === 'success' && result.data) {
              
              setResponse(result.data);
              
              
              if (result.data.order && result.data.order.items) {
                console.log('현재 주문:', currentOrder);
                console.log('새 주문 데이터:', result.data.order);
                
                
                setCurrentOrder(result.data.order);
              }
              
              
              if (result.data.needs_clarification && result.data.clarification_items && result.data.clarification_items.length > 0) {
                console.log('명확화 항목 감지:', result.data.clarification_items[0]);
                
                
                if (result.data.is_casual_conversation) {
                  console.log('일상 대화 감지됨, 명확화 상태 유지');
                  
                  setStatus('추가 정보를 마이크 버튼을 눌러 음성으로 알려주세요');
                  setNeedsClarification(true);
                  setClarificationItem(result.data.clarification_items[0]);
                } else {
                  
                  setNeedsClarification(true);
                  setClarificationItem(result.data.clarification_items[0]);
                  
                  setStatus('추가 정보를 마이크 버튼을 눌러 음성으로 알려주세요');
                }
              } else {
                
                setClarificationMode(false);
                setNeedsClarification(false);
                setClarificationItem('');
                
                
                if (result.data.message.includes("더 주문하실 것이 있으신가요")) {
                  setStatus('주문이 추가되었습니다. 더 주문하실 것이 있으신가요?');
                } else {
                  setStatus(result.data.message);
                }
              }
            } else {
              throw new Error('서버 응답 형식이 올바르지 않습니다');
            }
          }
          
          else {
            setStatus('주문 분석 중...');
            const result = await analyzeOrder(audioBlob);
            console.log('서버 응답 수신:', result);
            
            if (result.status === 'success' && result.data) {
              
              setResponse(result.data);
              
              
              if (result.data.order && result.data.order.items) {
                console.log('현재 주문:', currentOrder);
                console.log('새 주문 데이터:', result.data.order);
                
                
                setCurrentOrder(result.data.order);
              }
              
              
              if (result.data.is_casual_conversation) {
                console.log('일상적인 대화 감지:', result.data.message);
                setStatus('대화 중...');
                
                setNeedsClarification(false);
                setClarificationItem('');
              }
              
              else if (result.data.needs_clarification && result.data.clarification_items && result.data.clarification_items.length > 0) {
                const clarification = result.data.clarification_items[0];
                
                if (clarification.includes("더 주문하실 것이") || clarification.includes("더 주문")) {
                  setNeedsClarification(false);
                  setStatus(clarification);
                } else {
                  
                  setNeedsClarification(true);
                  setClarificationMode(true);
                  setClarificationItem(clarification);
                  setStatus('추가 정보를 마이크 버튼을 눌러 음성으로 알려주세요');
                }
              } else {
                
                setNeedsClarification(false);
                setClarificationItem('');
                setStatus(result.data.message || '주문이 추가되었습니다. 더 주문하실 것이 있으신가요?');
              }
            } else {
              throw new Error('서버 응답 형식이 올바르지 않습니다');
            }
          }
        } catch (err) {
          console.error('주문 처리 오류:', err);
          setStatus('처리에 실패했습니다. 다시 시도해주세요.');
          setHasError(true);
          processedAudioRef.current = false; 
        } finally {
          setIsLoading(false);
        }
      }
    };
    
    processAudio();
  }, [isListening, audioBlob, clarificationMode, currentOrder]);

  const handleMicrophoneClick = () => {
    if (isListening) {
      stopListening();
      if (clarificationMode) {
        setStatus('추가 정보 처리 중...');
      } else {
        setStatus('음성 분석 중...');
      }
    } else {
      resetAudio();
      processedAudioRef.current = false; 
      
      if (clarificationMode) {
        setStatus('추가 정보를 말씀해주세요...');
      } else {
        setStatus('듣고 있습니다...');
        
        if (!response || !response.is_casual_conversation) {
          setResponse(null);
          setNeedsClarification(false);
          setClarificationItem('');
        }
      }
      startListening();
    }
  };

  const handleClose = () => {
    if (isListening) {
      stopListening();
    }
    resetAudio();
    processedAudioRef.current = false;
    
    
    
    if (currentOrder && currentOrder.items && currentOrder.items.length > 0) {
      console.log('주문 세션 완료:', currentOrder);
      if (onOrderComplete) {
        
        const completeResponse = {
          ...response,
          order: {
            ...currentOrder,
            order_complete: true
          }
        };
        onOrderComplete(completeResponse);
      }
    } else {
      
      console.log('주문 없이 세션 종료');
      onClose();
    }
  };

  const speakMessage = (text) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'ko-KR';
      window.speechSynthesis.speak(utterance);
    } else {
      console.log('이 브라우저는 음성 합성을 지원하지 않습니다.');
    }
  };

  // 응답이 업데이트될 때 TTS로
  useEffect(() => {
    if (response && response.message) {
      speakMessage(response.message);
    }
  }, [response]);

  return (
    <AnimatePresence>
      {isOpen && (
        <ModalOverlay
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
        >
          <CloseButton 
            onClick={handleClose}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <FaTimes />
          </CloseButton>
          
          <ModalContent>
            <VoiceWaveContainer>
              {isListening && (
                <>
                  <WaveCircle
                    animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0.2, 0] }}
                    transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                  />
                  <WaveCircle
                    animate={{ scale: [1, 2, 1], opacity: [0.5, 0.2, 0] }}
                    transition={{ repeat: Infinity, duration: 3, ease: "easeInOut", delay: 0.5 }}
                  />
                  <WaveCircle
                    animate={{ scale: [1, 2.5, 1], opacity: [0.5, 0.2, 0] }}
                    transition={{ repeat: Infinity, duration: 4, ease: "easeInOut", delay: 1 }}
                  />
                </>
              )}
              
              <MicrophoneButton
                onClick={handleMicrophoneClick}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                animate={isListening ? { 
                  scale: [1, 1.1, 1], 
                  backgroundColor: ['#4fb477', '#ff6b6b', '#4fb477']
                } : {}}
                transition={isListening ? { repeat: Infinity, duration: 1.5 } : {}}
              >
                <FaMicrophone />
              </MicrophoneButton>
            </VoiceWaveContainer>
            
            {hasError ? (
              <StatusText
                animate={{ opacity: 1 }}
                initial={{ opacity: 0 }}
              >
                {status}
              </StatusText>
            ) : (
              <StatusText
                animate={{ opacity: 1 }}
                initial={{ opacity: 0 }}
              >
                {isLoading ? "처리 중..." : status}
              </StatusText>
            )}
            
            {response && (
              <ResponseText
                animate={{ opacity: 1 }}
                initial={{ opacity: 0 }}
              >
                {}
                {response.is_casual_conversation ? (
                  <span style={{ color: '#ffffff' }}>{response.message}</span>
                ) : (
                  response.message
                )}
                
                {needsClarification && (
                  <InstructionText style={{ marginTop: '1rem', display: 'block' }}>
                    마이크 버튼을 누르고 추가 정보를 말씀해주세요
                  </InstructionText>
                )}
              </ResponseText>
            )}
            
            {}
            {currentOrder && currentOrder.items && currentOrder.items.length > 0 && (
              <ResponseText
                animate={{ opacity: 1 }}
                initial={{ opacity: 0 }}
                style={{ fontSize: '1.2rem', marginTop: '1rem', color: 'rgba(255, 255, 255, 0.8)' }}
              >
                <div>현재 주문 내역:</div>
                {currentOrder.items.map((item, index) => (
                  <div key={index}>
                    {item.name} x {item.quantity} {item.options && item.options.length > 0 ? `(${item.options.join(', ')})` : ''}
                  </div>
                ))}
                <div style={{ marginTop: '0.5rem' }}>
                  총 금액: {currentOrder.total_price}원
                </div>
              </ResponseText>
            )}
          </ModalContent>
        </ModalOverlay>
      )}
    </AnimatePresence>
  );
};

export default VoiceModal;
