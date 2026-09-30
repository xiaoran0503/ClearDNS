import React from 'react';

interface GeoCellProps {
    answerGeo?: string;
}

const GeoCell = ({ answerGeo }: GeoCellProps) => {
    const text = answerGeo || '-';

    return (
        <div className="logs__cell logs__cell--geo text-truncate" role="gridcell" title={text}>
            <div className="logs__text text-truncate">{text}</div>
        </div>
    );
};

export default GeoCell;
