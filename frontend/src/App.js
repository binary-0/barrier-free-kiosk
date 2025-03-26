import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import Header from './components/Header';
import MenuCategory from './components/MenuCategory';
import VoiceModal from './components/VoiceModal';
import OrderSummary from './components/OrderSummary';
import { fetchMenus } from './services/api';

const MainContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
`;

const LoadingScreen = styled(motion.div)`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 60vh;
  font-size: 1.5rem;
  color: var(--primary-color);
`;

const ErrorScreen = styled(motion.div)`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 60vh;
  color: var(--error-color);
  text-align: center;
`;

const RefreshButton = styled(motion.button)`
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  
  &:hover {
    background-color: #3e5d8a;
  }
`;

const App = () => {
  const [menuData, setMenuData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false);
  const [orderData, setOrderData] = useState(null);
  const [cartCount, setCartCount] = useState(0);

  useEffect(() => {
    loadMenuData();
  }, []);
  
  // 주문 데이터가 변경될 때마다 카트 수량 업데이트
  useEffect(() => {
    if (orderData && orderData.order && orderData.order.items) {
      const count = orderData.order.items.reduce((total, item) => total + item.quantity, 0);
      setCartCount(count);
    }
  }, [orderData]);

  const loadMenuData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetchMenus();
      setMenuData(response.data);
      setLoading(false);
    } catch (err) {
      console.error('메뉴 로딩 실패:', err);
      setError('메뉴를 불러오는데 실패했습니다. 다시 시도해주세요.');
      setLoading(false);
    }
  };

  const handleVoiceButtonClick = () => {
    setIsVoiceModalOpen(true);
  };

  const handleCloseVoiceModal = () => {
    setIsVoiceModalOpen(false);
  };

  const handleOrderComplete = (data) => {
    setOrderData(data);
    setTimeout(() => {
      setIsVoiceModalOpen(false);
    }, 1000);
  };

  return (
    <div className="App">
      <Header onVoiceButtonClick={handleVoiceButtonClick} cartItems={cartCount} />
      
      <MainContainer>
        <AnimatePresence>
          {orderData && (
            <OrderSummary order={orderData} />
          )}
        </AnimatePresence>
        
        {loading ? (
          <LoadingScreen
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            메뉴를 불러오는 중...
          </LoadingScreen>
        ) : error ? (
          <ErrorScreen
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <div>{error}</div>
            <RefreshButton 
              onClick={loadMenuData}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              다시 시도하기
            </RefreshButton>
          </ErrorScreen>
        ) : (
          menuData.map(category => (
            <MenuCategory 
              key={category.id} 
              category={category} 
            />
          ))
        )}
      </MainContainer>
      
      <VoiceModal 
        isOpen={isVoiceModalOpen} 
        onClose={handleCloseVoiceModal}
        onOrderComplete={handleOrderComplete}
      />
    </div>
  );
};

export default App; 