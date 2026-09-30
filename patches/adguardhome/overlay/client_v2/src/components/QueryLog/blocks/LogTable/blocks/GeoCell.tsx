import cn from 'clsx';

import theme from 'panel/lib/theme';
import type { NormalizedQueryLogItem } from 'panel/helpers/helpers';

import s from '../LogTable.module.pcss';

type Props = {
    row: NormalizedQueryLogItem;
};

export const GeoCell = (props: Props) => {
    const text = () => props.row.response?.find((item) => item.geo)?.geo || '-';

    return (
        <div class={s.geoCell} title={text()}>
            <span class={cn(theme.text.t3, s.geoLabel)}>{text()}</span>
        </div>
    );
};
