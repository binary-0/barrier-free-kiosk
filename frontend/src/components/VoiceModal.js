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

// 명확화 관련 스타일 대체
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

const InstructionText = styled.p`
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 1rem;
  margin-bottom: 2rem;
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
      // 새 세션이 시작될 때마다 현재 주문 초기화 - 이 부분 유지
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
      // 이미 처리된 오디오 블롭이면 중복 처리 방지
      if (!isListening && audioBlob && audioBlob.size > 0 && !processedAudioRef.current) {
        processedAudioRef.current = true; // 처리 중인 오디오 표시
        setIsLoading(true);
        setHasError(false);
        
        try {
          console.log(`서버로 오디오 파일 전송 시작 (${audioBlob.size} bytes)`);
          
          // 명확화 모드인 경우 명확화 응답 전송
          if (clarificationMode) {
            setStatus('추가 정보 처리 중...');
            const result = await respondToClarification(audioBlob);
            console.log('명확화 응답 결과:', result);
            
            if (result.status === 'success' && result.data) {
              // 서버 응답 저장 - 명확화 항목이 있으면 response.message를 대체
              if (result.data.needs_clarification && result.data.clarification_items && result.data.clarification_items.length > 0) {
                setResponse({
                  ...result.data,
                  message: result.data.clarification_items[0]
                });
              } else {
                setResponse(result.data);
              }
              
              // 주문 상태 업데이트
              if (result.data.order && result.data.order.items) {
                console.log('현재 주문:', currentOrder);
                console.log('새 주문 데이터:', result.data.order);
                
                // 주문 정보 업데이트 (누적)
                setCurrentOrder(result.data.order);
              }
              
              // 일상 대화인 경우 기존 명확화 상태를 유지
              if (result.data.is_casual_conversation) {
                console.log('일상 대화 감지됨, 명확화 상태 유지');
                // 명확화 상태 유지 (원래 상태로 돌아감)
                setStatus('추가 정보를 마이크 버튼을 눌러 음성으로 알려주세요');
                
                // 명확화 아이템이 있는 경우 계속 표시하지만 별도 컨테이너로 보여주지 않음
                if (result.data.clarification_items && result.data.clarification_items.length > 0) {
                  setNeedsClarification(true);
                  setClarificationItem(result.data.clarification_items[0]);
                }
              }
              // 추가 명확화 필요 여부 확인 (일상 대화가 아닌 경우만)
              else if (result.data.needs_clarification && result.data.clarification_items && result.data.clarification_items.length > 0) {
                setNeedsClarification(true);
                setClarificationItem(result.data.clarification_items[0]);
                // 명확화 모드 유지
                setStatus('추가 정보를 마이크 버튼을 눌러 음성으로 알려주세요');
              } else {
                // 명확화 항목 처리 완료
                setClarificationMode(false);
                setNeedsClarification(false);
                setClarificationItem('');
                
                // 백엔드에서 항상 should_continue_ordering은 true로 반환
                setStatus('주문이 추가되었습니다. 더 주문하실 것이 있으신가요?');
              }
            } else {
              throw new Error('서버 응답 형식이 올바르지 않습니다');
            }
          }
          // 일반 주문 분석 모드
          else {
            setStatus('주문 분석 중...');
            const result = await analyzeOrder(audioBlob);
            console.log('서버 응답 수신:', result);
            
            if (result.status === 'success' && result.data) {
              // 명확화 항목이 있으면 response.message를 대체
              if (result.data.needs_clarification && result.data.clarification_items && result.data.clarification_items.length > 0) {
                // 서버 응답 저장 (메시지 대체)
                setResponse({
                  ...result.data,
                  message: result.data.clarification_items[0]
                });
              } else {
                // 서버 응답 그대로 저장
                setResponse(result.data);
              }
              
              // 주문 상태 업데이트
              if (result.data.order && result.data.order.items) {
                console.log('현재 주문:', currentOrder);
                console.log('새 주문 데이터:', result.data.order);
                
                // 주문 정보 업데이트 (누적)
                setCurrentOrder(result.data.order);
              }
              
              // 일상적인 대화인지 확인
              if (result.data.is_casual_conversation) {
                console.log('일상적인 대화 감지:', result.data.message);
                setStatus('대화 중...');
                // 일상적인 대화인 경우에는 명확화 UI를 숨김
                setNeedsClarification(false);
                setClarificationItem('');
              }
              // 주문 관련 대화인 경우 처리
              else if (result.data.needs_clarification && result.data.clarification_items && result.data.clarification_items.length > 0) {
                const clarification = result.data.clarification_items[0];
                // "더 주문하실 것이 있으신가요?"라는 질문이면 일반적인 스타일로 표시
                if (clarification.includes("더 주문하실 것이") || clarification.includes("더 주문")) {
                  setNeedsClarification(false);
                  setStatus(clarification);
                } else {
                  // 명확화 필요 여부 처리
                  setNeedsClarification(true);
                  setClarificationMode(true);
                  setClarificationItem(clarification);
                  setStatus('추가 정보를 마이크 버튼을 눌러 음성으로 알려주세요');
                }
              } else {
                // 명확화 항목이 없는 경우
                setStatus('주문이 추가되었습니다. 더 주문하실 것이 있으신가요?');
              }
            } else {
              throw new Error('서버 응답 형식이 올바르지 않습니다');
            }
          }
        } catch (err) {
          console.error('주문 처리 오류:', err);
          setStatus('처리에 실패했습니다. 다시 시도해주세요.');
          setHasError(true);
          processedAudioRef.current = false; // 오류 발생 시 재시도 가능하도록 설정
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
      processedAudioRef.current = false; // 새로운 오디오 녹음 시작 시 처리 상태 초기화
      
      if (clarificationMode) {
        setStatus('추가 정보를 말씀해주세요...');
      } else {
        setStatus('듣고 있습니다...');
        // 새 주문 항목 추가 시 상태 초기화 (일상적인 대화 이후에는 초기화하지 않음)
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
    
    // X 버튼을 누르면 세션 종료 및 주문 완료 처리
    // 주문 내역이 있으면 완료 처리
    if (currentOrder && currentOrder.items && currentOrder.items.length > 0) {
      console.log('주문 세션 완료:', currentOrder);
      if (onOrderComplete) {
        // 주문 완료 상태로 변경하여 전달
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
      // 주문 내역이 없으면 그냥 닫기
      console.log('주문 없이 세션 종료');
      onClose();
    }
  };

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
                {/* 일상 대화인 경우 응답 메시지를 강조 표시 */}
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
            
            {/* 현재 주문 내역 요약 표시 */}
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