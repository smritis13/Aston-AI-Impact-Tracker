import React, { useState } from 'react';
import { Form, Row, Col } from 'react-bootstrap';

const PRESETS = [
  { value: 'thisYear', label: 'This Year' },
  { value: 'lastYear', label: 'Last Year' },
  { value: 'thisMonth', label: 'This Month' },
  { value: 'lastMonth', label: 'Last Month' },
  { value: 'monthRange', label: 'Custom Month Range' },
  { value: 'yearRange', label: 'Custom Year Range' },
  { value: 'custom', label: 'Custom Dates' },
];

function getThisYearRange() {
  const now = new Date();
  const start = new Date(now.getFullYear(), 0, 1);
  const end = new Date(now.getFullYear(), 11, 31);
  return {
    startDate: start.toISOString().slice(0, 10),
    endDate: end.toISOString().slice(0, 10),
  };
}
function getLastYearRange() {
  const now = new Date();
  const start = new Date(now.getFullYear() - 1, 0, 1);
  const end = new Date(now.getFullYear() - 1, 11, 31);
  return {
    startDate: start.toISOString().slice(0, 10),
    endDate: end.toISOString().slice(0, 10),
  };
}
function getThisMonthRange() {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), 1);
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  return {
    startDate: start.toISOString().slice(0, 10),
    endDate: end.toISOString().slice(0, 10),
  };
}
function getLastMonthRange() {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  const end = new Date(now.getFullYear(), now.getMonth(), 0);
  return {
    startDate: start.toISOString().slice(0, 10),
    endDate: end.toISOString().slice(0, 10),
  };
}

const months = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];

const years = Array.from({ length: 20 }, (_, i) => new Date().getFullYear() - i);

type DateRangeWidgetValue = {
  preset: string;
  dateRange: { startDate: string; endDate: string };
  monthRange: { startMonth: number; startYear: number; endMonth: number; endYear: number };
  yearRange: { startYear: number; endYear: number };
};

interface DateRangeWidgetProps {
  value: DateRangeWidgetValue;
  onChange: (value: DateRangeWidgetValue) => void;
}

const DateRangeWidget: React.FC<DateRangeWidgetProps> = ({ value, onChange }) => {
  const [preset, setPreset] = useState<string>(value?.preset || 'thisYear');
  const [dateRange, setDateRange] = useState<{ startDate: string; endDate: string }>(value?.dateRange || getThisYearRange());
  const [monthRange, setMonthRange] = useState<{ startMonth: number; startYear: number; endMonth: number; endYear: number }>(value?.monthRange || { startMonth: 0, startYear: years[0], endMonth: 0, endYear: years[0] });
  const [yearRange, setYearRange] = useState<{ startYear: number; endYear: number }>(value?.yearRange || { startYear: years[0], endYear: years[0] });

  // Handle preset change
  const handlePresetChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setPreset(val);
    let newRange = {} as { startDate: string; endDate: string };
    if (val === 'thisYear') newRange = getThisYearRange();
    else if (val === 'lastYear') newRange = getLastYearRange();
    else if (val === 'thisMonth') newRange = getThisMonthRange();
    else if (val === 'lastMonth') newRange = getLastMonthRange();
    else if (val === 'monthRange') newRange = monthRangeToDates(monthRange);
    else if (val === 'yearRange') newRange = yearRangeToDates(yearRange);
    else newRange = dateRange;
    setDateRange(newRange);
    onChange && onChange({ preset: val, dateRange: newRange, monthRange, yearRange });
  };

  // Month range to dates
  function monthRangeToDates({ startMonth, startYear, endMonth, endYear }: { startMonth: number; startYear: number; endMonth: number; endYear: number }) {
    const start = new Date(startYear, startMonth, 1);
    const end = new Date(endYear, endMonth + 1, 0);
    return {
      startDate: start.toISOString().slice(0, 10),
      endDate: end.toISOString().slice(0, 10),
    };
  }
  // Year range to dates
  function yearRangeToDates({ startYear, endYear }: { startYear: number; endYear: number }) {
    const start = new Date(startYear, 0, 1);
    const end = new Date(endYear, 11, 31);
    return {
      startDate: start.toISOString().slice(0, 10),
      endDate: end.toISOString().slice(0, 10),
    };
  }

  // Handlers for custom pickers
  const handleMonthRangeChange = (field: string, val: number) => {
    const updated = { ...monthRange, [field]: val };
    setMonthRange(updated);
    const newRange = monthRangeToDates(updated);
    setDateRange(newRange);
    onChange && onChange({ preset: 'monthRange', dateRange: newRange, monthRange: updated, yearRange });
  };
  const handleYearRangeChange = (field: string, val: number) => {
    const updated = { ...yearRange, [field]: val };
    setYearRange(updated);
    const newRange = yearRangeToDates(updated);
    setDateRange(newRange);
    onChange && onChange({ preset: 'yearRange', dateRange: newRange, monthRange, yearRange: updated });
  };
  const handleDateChange = (field: string, val: string) => {
    const updated = { ...dateRange, [field]: val };
    setDateRange(updated);
    onChange && onChange({ preset: 'custom', dateRange: updated, monthRange, yearRange });
  };

  return (
    <Form.Group>
      <Form.Label>Date Filter</Form.Label>
      <Form.Select value={preset} onChange={handlePresetChange}>
        {PRESETS.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </Form.Select>
      {preset === 'monthRange' && (
        <Row className="g-2 mt-2">
          <Col>
            <Form.Label>Start Month</Form.Label>
            <Form.Select value={monthRange.startMonth} onChange={e => handleMonthRangeChange('startMonth', parseInt(e.target.value))}>
              {months.map((m, i) => <option key={m} value={i}>{m}</option>)}
            </Form.Select>
          </Col>
          <Col>
            <Form.Label>Start Year</Form.Label>
            <Form.Select value={monthRange.startYear} onChange={e => handleMonthRangeChange('startYear', parseInt(e.target.value))}>
              {years.map(y => <option key={y} value={y}>{y}</option>)}
            </Form.Select>
          </Col>
          <Col>
            <Form.Label>End Month</Form.Label>
            <Form.Select value={monthRange.endMonth} onChange={e => handleMonthRangeChange('endMonth', parseInt(e.target.value))}>
              {months.map((m, i) => <option key={m} value={i}>{m}</option>)}
            </Form.Select>
          </Col>
          <Col>
            <Form.Label>End Year</Form.Label>
            <Form.Select value={monthRange.endYear} onChange={e => handleMonthRangeChange('endYear', parseInt(e.target.value))}>
              {years.map(y => <option key={y} value={y}>{y}</option>)}
            </Form.Select>
          </Col>
        </Row>
      )}
      {preset === 'yearRange' && (
        <Row className="g-2 mt-2">
          <Col>
            <Form.Label>Start Year</Form.Label>
            <Form.Select value={yearRange.startYear} onChange={e => handleYearRangeChange('startYear', parseInt(e.target.value))}>
              {years.map(y => <option key={y} value={y}>{y}</option>)}
            </Form.Select>
          </Col>
          <Col>
            <Form.Label>End Year</Form.Label>
            <Form.Select value={yearRange.endYear} onChange={e => handleYearRangeChange('endYear', parseInt(e.target.value))}>
              {years.map(y => <option key={y} value={y}>{y}</option>)}
            </Form.Select>
          </Col>
        </Row>
      )}
      {preset === 'custom' && (
        <Row className="g-2 mt-2">
          <Col>
            <Form.Label>Start Date</Form.Label>
            <Form.Control type="date" value={dateRange.startDate} onChange={e => handleDateChange('startDate', e.target.value)} />
          </Col>
          <Col>
            <Form.Label>End Date</Form.Label>
            <Form.Control type="date" value={dateRange.endDate} onChange={e => handleDateChange('endDate', e.target.value)} />
          </Col>
        </Row>
      )}
    </Form.Group>
  );
};

export default DateRangeWidget; 