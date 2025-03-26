import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import MenuItem from './MenuItem';

const CategorySection = styled.section`
  margin-bottom: 2rem;
`;

const CategoryTitle = styled(motion.h2)`
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--primary-color);
  color: var(--primary-color);
  font-size: 1.5rem;
`;

const CategoryDescription = styled.p`
  color: var(--gray);
  margin-bottom: 1.5rem;
  font-size: 1rem;
`;

const ItemsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
`;

const MenuCategory = ({ category, onSelectItem }) => {
  return (
    <CategorySection>
      <CategoryTitle
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
      >
        {category.name}
      </CategoryTitle>
      <CategoryDescription>{category.description}</CategoryDescription>
      
      <ItemsGrid>
        {category.items.map((item, index) => (
          <MenuItem 
            key={item.id} 
            item={item} 
            onClick={onSelectItem}
            style={{ animationDelay: `${index * 0.1}s` }}
          />
        ))}
      </ItemsGrid>
    </CategorySection>
  );
};

export default MenuCategory; 