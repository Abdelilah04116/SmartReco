import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ScoreBadge from './ScoreBadge';
import { CustomerScore } from '../services/api';

interface DataTableProps {
  data: CustomerScore[];
  onRowClick?: (customer: CustomerScore) => void;
}

const DataTable = ({ data, onRowClick }: DataTableProps) => {
  const [sortField, setSortField] = useState<keyof CustomerScore | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const navigate = useNavigate();

  const handleSort = (field: keyof CustomerScore) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const sortedData = [...data].sort((a, b) => {
    if (!sortField) return 0;
    
    const aValue = a[sortField];
    const bValue = b[sortField];
    
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
    }
    
    const aStr = String(aValue);
    const bStr = String(bValue);
    return sortDirection === 'asc'
      ? aStr.localeCompare(bStr)
      : bStr.localeCompare(aStr);
  });

  const handleRowClick = (customer: CustomerScore) => {
    if (onRowClick) {
      onRowClick(customer);
    } else {
      navigate(`/customer/${customer.customer_id}`);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('customer_id')}
              >
                Customer ID
                {sortField === 'customer_id' && (
                  <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('priority_score')}
              >
                Score
                {sortField === 'priority_score' && (
                  <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('priority_label')}
              >
                Priority
                {sortField === 'priority_label' && (
                  <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Rules Fired
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Age
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Balance
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedData.map((customer, index) => (
              <tr
                key={customer.customer_id || index}
                className="hover:bg-gray-50 cursor-pointer transition-colors"
                onClick={() => handleRowClick(customer)}
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {customer.customer_id}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {customer.priority_score.toFixed(2)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <ScoreBadge label={customer.priority_label} score={customer.priority_score} />
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {customer.rules_fired.length} rule{customer.rules_fired.length !== 1 ? 's' : ''}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {customer.raw_data?.age || 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {customer.raw_data?.balance ? `$${customer.raw_data.balance.toLocaleString()}` : 'N/A'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No customers found
        </div>
      )}
    </div>
  );
};

export default DataTable;


