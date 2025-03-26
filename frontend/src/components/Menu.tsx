import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';

interface MenuItem {
  id: number;
  name: string;
  description: string;
  price: number;
  category: string;
  options: string[];
}

interface MenuProps {
  items: MenuItem[];
  onItemSelect: (item: MenuItem) => void;
}

const MenuContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 2rem;
  padding: 2rem;
  background: #f8f9fa;
`;

const MenuCard = styled(motion.div)`
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.2s;

  &:hover {
    transform: translateY(-5px);
  }
`;

const ItemName = styled.h3`
  margin: 0;
  color: #2c3e50;
  font-size: 1.5rem;
`;

const ItemDescription = styled.p`
  color: #7f8c8d;
  margin: 0.5rem 0;
`;

const ItemPrice = styled.div`
  color: #e74c3c;
  font-size: 1.25rem;
  font-weight: bold;
  margin-top: 1rem;
`;

const CategoryTag = styled.span`
  background: #3498db;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.875rem;
  margin-bottom: 1rem;
  display: inline-block;
`;

const Menu: React.FC<MenuProps> = ({ items, onItemSelect }) => {
  return (
    <MenuContainer>
      {items.map((item) => (
        <MenuCard
          key={item.id}
          onClick={() => onItemSelect(item)}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <CategoryTag>{item.category}</CategoryTag>
          <ItemName>{item.name}</ItemName>
          <ItemDescription>{item.description}</ItemDescription>
          <ItemPrice>₩{item.price.toLocaleString()}</ItemPrice>
        </MenuCard>
      ))}
    </MenuContainer>
  );
};

export default Menu; 