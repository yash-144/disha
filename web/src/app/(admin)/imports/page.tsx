'use client';

import React, { useEffect, useState } from 'react';
import { adminApi, AdminImportItem } from '@/features/admin/services/adminApi';
import { AdminNav } from '@/features/admin/components/AdminNav';

export default function AdminImportsPage() {
  const [imports, setImports] = useState<AdminImportItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminApi.getImports()
      .then((res) => {
        setImports(res || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Data Ingestion Monitoring</h1>
        <p className="text-sm text-gray-500 mt-1">Track institutional data ingestion jobs, batches, and error validation</p>
      </div>

      <AdminNav />

      {loading ? (
        <div className="text-gray-500 py-12 text-center">Loading import jobs...</div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-100">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase">
                <th className="px-4 py-3">File Name</th>
                <th className="px-4 py-3">Source Type</th>
                <th className="px-4 py-3">Processed</th>
                <th className="px-4 py-3">Errors</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Created At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {imports.map((job) => (
                <tr key={job.id}>
                  <td className="px-4 py-3 font-medium text-gray-900">{job.file_name}</td>
                  <td className="px-4 py-3 text-gray-500">{job.source_type}</td>
                  <td className="px-4 py-3 text-gray-700">{job.processed_records} / {job.total_records}</td>
                  <td className="px-4 py-3 font-semibold text-red-600">{job.error_count}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-semibold ${
                      job.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                    }`}>
                      {job.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">{new Date(job.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

