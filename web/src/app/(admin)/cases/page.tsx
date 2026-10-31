'use client';

import React, { useEffect, useState } from 'react';
import { adminApi, AdminCaseItem } from '@/features/admin/services/adminApi';
import { AdminNav } from '@/features/admin/components/AdminNav';

export default function AdminCasesPage() {
  const [cases, setCases] = useState<AdminCaseItem[]>([]);
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    adminApi.getCases(overdueOnly)
      .then((res) => {
        setCases(res || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [overdueOnly]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Institutional Case Supervision</h1>
          <p className="text-sm text-gray-500 mt-1">Supervise caseloads, SLA deadlines, and interventions</p>
        </div>
        <button
          onClick={() => setOverdueOnly(!overdueOnly)}
          className={`px-4 py-2 text-sm font-semibold rounded-md border ${
            overdueOnly
              ? 'bg-red-600 text-white border-red-600'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
          }`}
        >
          {overdueOnly ? 'Showing Overdue Only' : 'Filter Overdue Cases'}
        </button>
      </div>

      <AdminNav />

      {loading ? (
        <div className="text-gray-500 py-12 text-center">Loading cases...</div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-100">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase">
                <th className="px-4 py-3">Case ID</th>
                <th className="px-4 py-3">Student</th>
                <th className="px-4 py-3">Assigned Counsellor</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">State</th>
                <th className="px-4 py-3">Due Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {cases.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                    No cases match the selected filter criteria.
                  </td>
                </tr>
              ) : (
                cases.map((c) => (
                  <tr key={c.id} className={c.is_overdue ? 'bg-red-50/40' : ''}>
                    <td className="px-4 py-3 font-mono font-medium text-indigo-600">{c.id}</td>
                    <td className="px-4 py-3 font-medium text-gray-900">
                      {c.student_name || c.student_id}
                      <div className="text-xs text-gray-400">{c.department}</div>
                    </td>
                    <td className="px-4 py-3 text-gray-700">{c.counsellor_name || 'Unassigned'}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold uppercase ${
                        c.priority === 'critical' ? 'bg-red-100 text-red-800' :
                        c.priority === 'high' ? 'bg-amber-100 text-amber-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {c.priority}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{c.state}</td>
                    <td className="px-4 py-3 text-xs text-gray-500">
                      {c.due_at ? new Date(c.due_at).toLocaleDateString() : 'N/A'}
                      {c.is_overdue && (
                        <span className="ml-2 font-bold text-red-600">OVERDUE</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

