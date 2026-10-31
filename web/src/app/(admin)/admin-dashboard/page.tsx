'use client';

import React, { useEffect, useState } from 'react';
import { adminApi, AdminDashboardData } from '@/features/admin/services/adminApi';
import { AdminNav } from '@/features/admin/components/AdminNav';

export default function AdminDashboardPage() {
  const [data, setData] = useState<AdminDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // In actual session, tokens and campusId are populated from AuthContext or session storage
    adminApi.getDashboard()
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        // Fallback demo indicator if unauthenticated in preview
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">DISHA Institutional Administration</h1>
        <p className="text-sm text-gray-500 mt-1">Real-time Student Early-Warning & Support CRM Supervision</p>
      </div>

      <AdminNav />

      {loading && <div className="text-gray-500 py-12 text-center">Loading administrative metrics...</div>}

      {error && (
        <div className="bg-amber-50 border-l-4 border-amber-400 p-4 mb-6">
          <p className="text-sm text-amber-700">
            Note: Authentication token required for live data stream ({error}). Connect session or visit with active institution administrator JWT.
          </p>
        </div>
      )}

      {data && (
        <div className="space-y-8">
          {/* Key Metrics Grid */}
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <div className="bg-white overflow-hidden shadow rounded-lg p-5 border border-gray-100">
              <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Total Enrolled Students</dt>
              <dd className="mt-2 text-3xl font-extrabold text-gray-900">{data.total_students}</dd>
            </div>
            <div className="bg-white overflow-hidden shadow rounded-lg p-5 border border-gray-100">
              <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Active Faculty & Counsellors</dt>
              <dd className="mt-2 text-3xl font-extrabold text-indigo-600">{data.total_faculty + data.total_counsellors}</dd>
              <p className="text-xs text-gray-400 mt-1">{data.total_counsellors} counsellors / {data.total_faculty} faculty</p>
            </div>
            <div className="bg-white overflow-hidden shadow rounded-lg p-5 border border-gray-100">
              <dt className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Active Supervised Cases</dt>
              <dd className="mt-2 text-3xl font-extrabold text-blue-600">{data.total_active_cases}</dd>
            </div>
            <div className="bg-white overflow-hidden shadow rounded-lg p-5 border border-red-100 bg-red-50/20">
              <dt className="text-xs font-semibold text-red-600 uppercase tracking-wider">SLA Overdue Cases</dt>
              <dd className="mt-2 text-3xl font-extrabold text-red-600">{data.overdue_cases}</dd>
            </div>
          </div>

          {/* Counsellor Workload Distribution */}
          <div className="bg-white shadow rounded-lg p-6 border border-gray-100">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Counsellor Workload & Capacity Overview</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead>
                  <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase">
                    <th className="px-4 py-3">Counsellor</th>
                    <th className="px-4 py-3">Department</th>
                    <th className="px-4 py-3">Active Cases</th>
                    <th className="px-4 py-3">Overdue</th>
                    <th className="px-4 py-3">Resolved</th>
                    <th className="px-4 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {data.counsellor_workload.map((cw) => (
                    <tr key={cw.user_id}>
                      <td className="px-4 py-3 font-medium text-gray-900">
                        {cw.full_name}
                        <div className="text-xs text-gray-400">{cw.email}</div>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{cw.department || 'General'}</td>
                      <td className="px-4 py-3 font-bold text-indigo-600">{cw.active_cases}</td>
                      <td className="px-4 py-3 text-red-600 font-semibold">{cw.overdue_cases}</td>
                      <td className="px-4 py-3 text-emerald-600 font-semibold">{cw.resolved_cases}</td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                          {cw.availability_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
