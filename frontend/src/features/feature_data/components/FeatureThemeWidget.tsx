import React, { useState } from 'react';
import { useTheme } from '../hooks/useTheme';
import FeatureThemeModal from './FeatureThemeModal';

interface FeatureThemeWidgetProps {
  themeId: number;
}

const FeatureThemeWidget: React.FC<FeatureThemeWidgetProps> = ({ themeId }) => {
  const [showFeatureModal, setShowFeatureModal] = useState(false);
  const { theme, toggleFeatured } = useTheme(themeId);

  if (!theme) return null;

  return (
    <>
      <button
        className="btn p-0 border-0 bg-transparent text-default"
        onClick={() => setShowFeatureModal(true)}
        title={theme.featured ? "Unfeature theme" : "Feature theme"}
      >
        <i className={`ri-star-${theme.featured ? 'fill' : 'line'} fs-5`}></i>
      </button>

      <FeatureThemeModal
        show={showFeatureModal}
        onHide={() => setShowFeatureModal(false)}
        theme={theme}
        onToggleFeatured={toggleFeatured}
      />
    </>
  );
};

export default FeatureThemeWidget; 