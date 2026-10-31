import React, { useState } from 'react'
import {
  Award,
  Package,
  CheckCircle2,
  Clock,
  XCircle,
  Filter,
  Search,
  Sparkles,
  ShoppingBag,
  Check,
  X,
} from 'lucide-react'
import {
  INITIAL_REDEMPTIONS,
  INITIAL_REWARD_CATALOG,
  RedemptionRecord,
  RewardCatalogItem,
} from './adminData'
import { useApp } from '../../context/AppContext'

export function AdminRewardFulfilmentPage() {
  const { addToast } = useApp()
  const [redemptions, setRedemptions] = useState<RedemptionRecord[]>(INITIAL_REDEMPTIONS)
  const [catalog, setCatalog] = useState<RewardCatalogItem[]>(INITIAL_REWARD_CATALOG)
  const [statusFilter, setStatusFilter] = useState('all')
  const [activeTab, setActiveTab] = useState<'redemptions' | 'stock'>('redemptions')
  const [searchQuery, setSearchQuery] = useState('')

  const filteredRedemptions = redemptions.filter((r) => {
    const matchesSearch =
      !searchQuery ||
      r.studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.studentRef.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.itemTitle.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesStatus = statusFilter === 'all' || r.status === statusFilter

    return matchesSearch && matchesStatus
  })

  // Approve Claim
  const handleApprove = (id: string) => {
    setRedemptions((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'approved' } : r))
    )
    addToast('Redemption Approved', 'Claim approved for campus distribution.', 'info')
  }

  // Mark Fulfilled
  const handleFulfill = (id: string) => {
    setRedemptions((prev) =>
      prev.map((r) =>
        r.id === id ? { ...r, status: 'fulfilled', fulfilledAt: 'Today' } : r
      )
    )
    addToast('Order Fulfilled', 'Student has received the reward item.', 'success')
  }

  // Cancel & Refund
  const handleCancel = (id: string) => {
    setRedemptions((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'cancelled' } : r))
    )
    addToast('Claim Cancelled', 'Redemption cancelled; points refunded to student ledger.', 'warning')
  }

  const getStatusBadge = (st: RedemptionRecord['status']) => {
    switch (st) {
      case 'requested':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">Pending Review</span>
      case 'approved':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">Approved for Pickup</span>
      case 'fulfilled':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Fulfilled</span>
      case 'cancelled':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">Cancelled / Refunded</span>
    }
  }

  return (
    <div className="flex flex-col gap-4 font-sans select-none">
      {/* 1. REWARD WORKSPACE HEADER */}
      <section className="bg-white rounded-3xl border border-gray-100/90 shadow-2xs p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-amber-50 text-amber-700 flex items-center justify-center shrink-0">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#1E2433] tracking-tight">
              Reward Fulfilment &amp; Points Ledger Workbench
            </h2>
            <p className="text-xs text-[#717E95]">
              Process student reward redemptions, maintain merchandise stock, and monitor participation ledgers (PTS-01 - RED-03)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center bg-gray-100 p-1 rounded-full text-xs font-semibold">
            <button
              type="button"
              onClick={() => setActiveTab('redemptions')}
              className={`px-3 py-1 rounded-full transition cursor-pointer ${
                activeTab === 'redemptions'
                  ? 'bg-white text-[#1E2433] shadow-xs font-bold'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Student Claims ({redemptions.filter((r) => r.status === 'requested').length} Pending)
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('stock')}
              className={`px-3 py-1 rounded-full transition cursor-pointer ${
                activeTab === 'stock'
                  ? 'bg-white text-[#1E2433] shadow-xs font-bold'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Merchandise Inventory
            </button>
          </div>
        </div>
      </section>

      {/* 2. STATS ROW */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        <div className="p-4 bg-white rounded-2xl border border-gray-100 shadow-2xs">
          <span className="text-xs font-semibold text-gray-500">Total Points Awarded (Campus Ledger)</span>
          <div className="text-2xl font-black text-[#1E2433] mt-1">42,850 pts</div>
          <span className="text-[10px] text-emerald-600 font-bold mt-1 block">✓ Decoupled from survey answers</span>
        </div>
        <div className="p-4 bg-white rounded-2xl border border-gray-100 shadow-2xs">
          <span className="text-xs font-semibold text-gray-500">Pending Fulfilment Claims</span>
          <div className="text-2xl font-black text-amber-600 mt-1">
            {redemptions.filter((r) => r.status === 'requested' || r.status === 'approved').length}
          </div>
          <span className="text-[10px] text-gray-400 mt-1 block">Apex Campus Distribution Counter</span>
        </div>
        <div className="p-4 bg-white rounded-2xl border border-gray-100 shadow-2xs">
          <span className="text-xs font-semibold text-gray-500">Active Catalogue SKUs</span>
          <div className="text-2xl font-black text-[#1E2433] mt-1">{catalog.length} Items</div>
          <span className="text-[10px] text-gray-400 mt-1 block">In stock &amp; claimable</span>
        </div>
      </div>

      {/* 3. TAB CONTENT */}
      {activeTab === 'redemptions' && (
        <div className="flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="relative max-w-md flex-1">
              <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by student name, ref or item title..."
                className="w-full text-xs pl-9 pr-4 py-2 bg-white rounded-full border border-gray-200 focus:outline-none shadow-2xs"
              />
            </div>

            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
              {[
                { id: 'all', label: 'All Redemptions' },
                { id: 'requested', label: 'Needs Approval' },
                { id: 'approved', label: 'Ready for Pickup' },
                { id: 'fulfilled', label: 'Fulfilled' },
              ].map((f) => (
                <button
                  key={f.id}
                  type="button"
                  onClick={() => setStatusFilter(f.id)}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold transition cursor-pointer whitespace-nowrap ${
                    statusFilter === f.id
                      ? 'bg-[#1E2433] text-white shadow-2xs'
                      : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Redemptions Table */}
          <div className="bg-white rounded-3xl border border-gray-100 shadow-2xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-gray-100 bg-[#FAFBFD] text-gray-500 font-bold uppercase tracking-wider text-[10px]">
                    <th className="py-3.5 px-4">Claim ID</th>
                    <th className="py-3.5 px-4">Student</th>
                    <th className="py-3.5 px-4">Reward Item / SKU</th>
                    <th className="py-3.5 px-4">Points Cost</th>
                    <th className="py-3.5 px-4">Date Claimed</th>
                    <th className="py-3.5 px-4">Status</th>
                    <th className="py-3.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredRedemptions.map((r) => (
                    <tr key={r.id} className="hover:bg-gray-50/70 transition">
                      <td className="py-3.5 px-4 font-mono font-bold text-[#1E2433]">
                        {r.id.toUpperCase()}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="font-bold text-[#1E2433] block">{r.studentName}</span>
                        <span className="text-[11px] text-gray-400 font-mono">{r.studentRef}</span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="font-semibold text-gray-800 block">{r.itemTitle}</span>
                        <span className="text-[10px] text-gray-400 font-mono">{r.sku}</span>
                      </td>
                      <td className="py-3.5 px-4 font-bold text-amber-700">
                        {r.pointsCost} pts
                      </td>
                      <td className="py-3.5 px-4 text-gray-600">
                        {r.requestedAt}
                      </td>
                      <td className="py-3.5 px-4">
                        {getStatusBadge(r.status)}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {r.status === 'requested' && (
                            <>
                              <button
                                type="button"
                                onClick={() => handleApprove(r.id)}
                                className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-blue-50 text-blue-700 hover:bg-blue-100 transition cursor-pointer"
                              >
                                Approve
                              </button>
                              <button
                                type="button"
                                onClick={() => handleCancel(r.id)}
                                className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-gray-100 text-rose-700 hover:bg-rose-50 transition cursor-pointer"
                              >
                                Decline
                              </button>
                            </>
                          )}
                          {r.status === 'approved' && (
                            <button
                              type="button"
                              onClick={() => handleFulfill(r.id)}
                              className="px-3 py-1 rounded-full text-[11px] font-bold bg-emerald-700 hover:bg-emerald-800 text-white transition cursor-pointer"
                            >
                              Mark Handed Over
                            </button>
                          )}
                          {r.status === 'fulfilled' && (
                            <span className="text-[11px] text-emerald-600 font-semibold">
                              ✓ Completed
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB: STOCK INVENTORY */}
      {activeTab === 'stock' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3.5">
          {catalog.map((item) => (
            <div
              key={item.id}
              className="p-5 rounded-3xl bg-white border border-gray-100 shadow-2xs flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-gray-100 text-gray-700">
                    {item.category}
                  </span>
                  <span className="text-xs font-bold text-amber-700">
                    {item.pointsCost} pts
                  </span>
                </div>
                <h4 className="text-xs font-bold text-[#1E2433] mt-3">
                  {item.title}
                </h4>
                <span className="text-[11px] font-mono text-gray-400 mt-0.5 block">
                  SKU: {item.sku}
                </span>
              </div>

              <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
                <span className="text-gray-500">In Stock:</span>
                <span className="font-bold text-[#1E2433]">{item.stock} units</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

