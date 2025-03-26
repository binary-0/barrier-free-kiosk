import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';

const MenuItemCard = styled(motion.div)`
  background-color: var(--white);
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 1.2rem;
  transition: transform var(--transition-speed), box-shadow var(--transition-speed);
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  cursor: pointer;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
  }
`;

const MenuImage = styled.div`
  height: 180px;
  background-color: var(--gray-light);
  background-image: ${props => props.imageUrl ? `url(${props.imageUrl})` : 'none'};
  background-size: cover;
  background-position: center;
  border-radius: var(--border-radius);
  margin-bottom: 0.8rem;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.05);
    z-index: 1;
  }
  
  /* 이미지가 없을 경우 표시할 기본 이미지 */
  &::after {
    content: ${props => !props.imageUrl ? "'🍽️'" : "none"};
    display: ${props => !props.imageUrl ? "flex" : "none"};
    justify-content: center;
    align-items: center;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    font-size: 3rem;
    color: var(--gray);
  }
`;

const MenuTitle = styled.h3`
  margin: 0.5rem 0;
  font-size: 1.2rem;
  color: var(--text-color);
`;

const MenuDescription = styled.p`
  color: var(--gray);
  font-size: 0.9rem;
  margin-bottom: 0.8rem;
  flex-grow: 1;
`;

const MenuPrice = styled.div`
  font-weight: bold;
  font-size: 1.1rem;
  color: var(--primary-color);
`;

const OptionsList = styled.div`
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: var(--gray);
`;

const MenuItem = ({ item, onClick }) => {
  const formatPrice = (price) => {
    return new Intl.NumberFormat('ko-KR').format(price);
  };

  return (
    <MenuItemCard
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.98 }}
      onClick={() => onClick && onClick(item)}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <MenuImage imageUrl={item.image_url} />
      <MenuTitle>{item.name}</MenuTitle>
      <MenuDescription>{item.description}</MenuDescription>
      <MenuPrice>{formatPrice(item.base_price)}원</MenuPrice>
      
      {item.options && item.options.length > 0 && (
        <OptionsList>
          옵션: {item.options.map(option => option.name).join(', ')}
        </OptionsList>
      )}
    </MenuItemCard>
  );
};

export default MenuItem; 