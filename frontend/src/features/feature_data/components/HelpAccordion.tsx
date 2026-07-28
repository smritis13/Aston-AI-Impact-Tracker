import React from 'react';
import { Accordion } from 'react-bootstrap';

interface HelpAccordionProps {
  helpText: {
    title: string;
    content: {
      description: string;
      steps: string[];
      footer: string;
    };
  };
}

const HelpAccordion: React.FC<HelpAccordionProps> = ({ helpText }) => {
  const steps = Array.isArray(helpText.content.steps) ? helpText.content.steps : [];

  return (
    <Accordion defaultActiveKey="" className="mb-4">
      <Accordion.Item eventKey="0">
        <Accordion.Header>{helpText.title}</Accordion.Header>
        <Accordion.Body>
          <p>{helpText.content.description}</p>
          <ol>
            {steps.map((step, index) => (
              <li key={index}>{step}</li>
            ))}
          </ol>
          <p>{helpText.content.footer}</p>
        </Accordion.Body>
      </Accordion.Item>
    </Accordion>
  );
};

export default HelpAccordion; 
