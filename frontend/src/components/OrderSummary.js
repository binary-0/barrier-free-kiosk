import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { FaCheck, FaShoppingBag } from 'react-icons/fa';

const SummaryContainer = styled(motion.div)`
  background-color: var(--white);
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 1.5rem;
  margin-bottom: 2rem;
`;

const SummaryTitle = styled.h2`
  color: var(--primary-color);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const ItemList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 1.5rem 0;
`;

const OrderItem = styled(motion.li)`
  display: flex;
  justify-content: space-between;
  padding: 0.8rem 0;
  border-bottom: 1px solid var(--gray-light);
  
  &:last-child {
    border-bottom: none;
  }
`;

const ItemDetails = styled.div`
  display: flex;
  flex-direction: column;
`;

const ItemName = styled.span`
  font-weight: 500;
`;

const ItemOptions = styled.span`
  font-size: 0.8rem;
  color: var(--gray);
  margin-top: 0.3rem;
`;

const ItemPrice = styled.span`
  font-weight: 500;
`;

const TotalSection = styled.div`
  display: flex;
  justify-content: space-between;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 2px solid var(--primary-color);
  font-weight: bold;
  font-size: 1.2rem;
`;

const CheckIcon = styled(FaCheck)`
  color: var(--success-color);
  margin-right: 0.5rem;
`;

const OrderSummary = ({ order }) => {
  if (!order || !order.order || !order.order.items) {
    return null;
  }
  
  const { items, total_price } = order.order;
  
  const formatPrice = (price) => {
    return new Intl.NumberFormat('ko-KR').format(price);
  };
  
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };
  
  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <SummaryContainer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <SummaryTitle>
        <FaShoppingBag /> 주문 내역
      </SummaryTitle>
      
      <ItemList variants={container} initial="hidden" animate="show">
        {items.map((item, index) => (
          <OrderItem key={index} variants={item}>
            <ItemDetails>
              <ItemName>
                {item.name} x {item.quantity}
              </ItemName>
              {item.options && item.options.length > 0 && (
                <ItemOptions>
                  옵션: {item.options.join(', ')}
                </ItemOptions>
              )}
            </ItemDetails>
            <ItemPrice>{formatPrice(item.price)}원</ItemPrice>
          </OrderItem>
        ))}
      </ItemList>
      
      <TotalSection>
        <span>총 금액</span>
        <span>{formatPrice(total_price)}원</span>
      </TotalSection>
      
      {!order.needs_clarification && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          style={{ marginTop: '1rem', color: 'var(--success-color)', display: 'flex', alignItems: 'center' }}
        >
          <CheckIcon /> 주문이 완료되었습니다
        </motion.div>
      )}
    </SummaryContainer>
  );
};

export default OrderSummary; 