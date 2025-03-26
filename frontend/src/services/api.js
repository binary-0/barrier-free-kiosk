import axios from 'axios';

// API 기본 설정
const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 세션 ID 관리
let sessionId = localStorage.getItem('session_id') || null;

export const setSessionId = (id) => {
  sessionId = id;
  localStorage.setItem('session_id', id);
};

export const getSessionId = () => sessionId;

export const clearSessionId = () => {
  sessionId = null;
  localStorage.removeItem('session_id');
};

// API 함수들
export const fetchMenus = async () => {
  try {
    const response = await api.get('/menu');
    return response.data;
  } catch (error) {
    console.error('Error fetching menus:', error);
    throw error;
  }
};

export const analyzeOrder = async (audioBlob) => {
  try {
    const formData = new FormData();
    // 타임스탬프를 포함한 고유한 파일명 생성
    const timestamp = Date.now();
    const uniqueFilename = `audio_recording_${timestamp}.webm`;
    formData.append('audio_file', audioBlob, uniqueFilename);
    
    const headers = {};
    if (sessionId) {
      headers['session-id'] = sessionId;
    }
    
    console.log(`음성 파일 전송: ${uniqueFilename}, 크기: ${audioBlob.size} bytes`);
    
    const response = await axios.post(`${API_BASE_URL}/analyze-order`, formData, {
      headers: {
        ...headers,
        'Content-Type': 'multipart/form-data',
      },
    });
    
    // 세션 ID 저장
    if (response.data.session_id) {
      setSessionId(response.data.session_id);
    }
    
    return response.data;
  } catch (error) {
    console.error('Error analyzing order:', error);
    throw error;
  }
};

export const respondToClarification = async (audioBlob) => {
  try {
    if (!sessionId) {
      throw new Error('세션이 없습니다. 새로운 주문을 시작해주세요.');
    }
    
    const formData = new FormData();
    // 타임스탬프를 포함한 고유한 파일명 생성
    const timestamp = Date.now();
    const uniqueFilename = `clarification_response_${timestamp}.webm`;
    formData.append('audio_file', audioBlob, uniqueFilename);
    
    console.log(`명확화 응답 음성 파일 전송: ${uniqueFilename}, 크기: ${audioBlob.size} bytes`);
    
    const response = await axios.post(`${API_BASE_URL}/respond-clarification`, formData, {
      headers: {
        'session-id': sessionId,
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  } catch (error) {
    console.error('Error responding to clarification:', error);
    throw error;
  }
};

export default api; 