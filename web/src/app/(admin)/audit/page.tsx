'use client';

import React, { useEffect, useState } from 'react';
import { adminApi, AdminAuditItem } from '@/features/admin/services/adminApi';
import { AdminNav } from '@/features/admin/components/AdminNav';

export default function AdminAuditPage() {
  const [logs, setLogs] = useState<AdminAuditItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminApi.getAuditLogs()
      .then((res) => {
        setLogs(res || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Immutable Audit Trail</h1>
        <p className="text-sm text-gray-500 mt-1">Cryptographically hash-chained event verification records</p>
      </div>

      <AdminNav />

      {loading ? (
        <div className="text-gray-500 py-12 text-center">Loading audit events...</div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-100">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase">
                <th className="px-4 py-3">Timestamp</th>
                <th className="px-4 py-3">Actor</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Entity</th>
                <th className="px-4 py-3">Hash Digest</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 font-mono text-xs">
              {logs.map((item) => (
                <tr key={item.id}>
                  <td className="px-4 py-3 text-gray-500">{new Date(item.created_at).toLocaleString()}</td>
                  <td className="px-4 py-3 text-gray-800">{item.actor_id}</td>
                  <td className="px-4 py-3 font-semibold text-indigo-600">{item.action}</td>
                  <td className="px-4 py-3 text-gray-600">{item.entity_type} ({item.entity_id})</td>
                  <td className="px-4 py-3 text-gray-400 truncate max-w-xs">{item.curr_hash || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

