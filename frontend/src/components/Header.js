import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { FaMicrophone, FaShoppingCart } from 'react-icons/fa';

const HeaderContainer = styled(motion.header)`
  background-color: var(--white);
  box-shadow: var(--box-shadow);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
`;

const Logo = styled.h1`
  color: var(--primary-color);
  font-size: 1.8rem;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const LogoIcon = styled.span`
  color: var(--accent-color);
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 1rem;
`;

const VoiceButton = styled(motion.button)`
  background-color: var(--accent-color);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  padding: 0.8rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  
  &:hover {
    background-color: #44a86b;
  }
  
  &:focus {
    outline: none;
  }
`;

const CartButton = styled(motion.button)`
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  padding: 0.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  cursor: pointer;
  
  &:hover {
    background-color: #3e5d8a;
  }
  
  &:focus {
    outline: none;
  }
`;

const Header = ({ onVoiceButtonClick, cartItems = 0 }) => {
  return (
    <HeaderContainer
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: 'spring', stiffness: 120, damping: 20 }}
    >
      <Logo>
        <LogoIcon>☕</LogoIcon> Cafe Le Blanc
      </Logo>
      
      <ActionButtons>
        <VoiceButton
          onClick={onVoiceButtonClick}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <FaMicrophone /> 음성으로 주문하기
        </VoiceButton>
        
        {cartItems > 0 && (
          <CartButton
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <FaShoppingCart /> {cartItems}
          </CartButton>
        )}
      </ActionButtons>
    </HeaderContainer>
  );
};

export default Header; 