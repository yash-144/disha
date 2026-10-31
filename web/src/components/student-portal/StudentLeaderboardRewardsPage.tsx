import React, { useState } from 'react'
import {
  Trophy,
  Gift,
  Flame,
  Award,
  Sparkles,
  CheckCircle2,
  Coffee,
  BookOpen,
  Dumbbell,
  Clock,
  Tag,
  Copy,
  Check,
  ChevronRight,
  Shield,
  Eye,
  EyeOff,
  ShoppingBag,
  Ticket,
} from 'lucide-react'
import { DemoMode } from './studentDemoData'

interface StudentLeaderboardRewardsPageProps {
  demoMode: DemoMode
}

interface BadgeItem {
  id: string
  title: string
  description: string
  icon: string
  earnedDate: string
  color: string
}

const EARNED_BADGES: BadgeItem[] = [
  {
    id: 'b-1',
    title: 'Streak Master',
    description: '3 consecutive weeks of emotional wellbeing check-ins',
    icon: '🔥',
    earnedDate: 'Earned 3 days ago',
    color: 'bg-amber-50 border-amber-200 text-amber-900',
  },
  {
    id: 'b-2',
    title: 'Mindful Breather',
    description: 'Completed 10 box breathing sessions in the portal',
    icon: '🌿',
    earnedDate: 'Earned last week',
    color: 'bg-emerald-50 border-emerald-200 text-emerald-900',
  },
  {
    id: 'b-3',
    title: 'Proactive Reachout',
    description: 'Initiated 1-on-1 mentor guidance consultation',
    icon: '🤝',
    earnedDate: 'Earned 14 Oct',
    color: 'bg-purple-50 border-purple-200 text-purple-900',
  },
  {
    id: 'b-4',
    title: 'Self-Care Pioneer',
    description: 'Completed term baseline and mid-term assessments',
    icon: '✨',
    earnedDate: 'Earned 09 Oct',
    color: 'bg-blue-50 border-blue-200 text-blue-900',
  },
]

interface LeaderboardUser {
  rank: number
  name: string
  degree: string
  avatar: string
  streakWeeks: number
  points: number
  isCurrentUser?: boolean
  badgesCount: number
}

const LEADERBOARD_DATA: LeaderboardUser[] = [
  {
    rank: 1,
    name: 'Siddharth Rao',
    degree: 'B.Tech (ECE) • 4th Year',
    avatar: 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=300&q=80',
    streakWeeks: 9,
    points: 1420,
    badgesCount: 8,
  },
  {
    rank: 2,
    name: 'Pooja Iyer',
    degree: 'B.Des (UI/UX) • 3rd Year',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=300&q=80',
    streakWeeks: 8,
    points: 1280,
    badgesCount: 7,
  },
  {
    rank: 3,
    name: 'Kabir Das',
    degree: 'B.Tech (CSE) • 2nd Year',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=300&q=80',
    streakWeeks: 7,
    points: 1150,
    badgesCount: 6,
  },
  {
    rank: 4,
    name: 'Ananya Deshmukh',
    degree: 'B.Arch • 4th Year',
    avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=300&q=80',
    streakWeeks: 6,
    points: 990,
    badgesCount: 5,
  },
  {
    rank: 5,
    name: 'Devansh Kulkarni',
    degree: 'B.Tech (Mech) • 3rd Year',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=300&q=80',
    streakWeeks: 5,
    points: 920,
    badgesCount: 5,
  },
  {
    rank: 14,
    name: 'Asha Verma',
    degree: 'B.Tech (CSE) • 3rd Year',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80',
    streakWeeks: 3,
    points: 850,
    badgesCount: 4,
    isCurrentUser: true,
  },
]

interface RewardItem {
  id: string
  title: string
  category: 'cafe' | 'books' | 'gym' | 'wellness'
  categoryLabel: string
  pointsCost: number
  description: string
  expiryDays: number
  stock: string
  icon: React.ComponentType<{ className?: string }>
}

const REWARDS_CATALOG: RewardItem[] = [
  {
    id: 'rew-1',
    title: 'Free Artisanal Coffee / Beverage',
    category: 'cafe',
    categoryLabel: 'Campus Central Cafe',
    pointsCost: 150,
    description: 'Enjoy a free espresso, cappuccino, or iced herbal tea at the Central Campus Cafe.',
    expiryDays: 30,
    stock: 'High availability',
    icon: Coffee,
  },
  {
    id: 'rew-2',
    title: '15% Off Textbooks & Stationery',
    category: 'books',
    categoryLabel: 'University Bookshop',
    pointsCost: 300,
    description: 'Valid for course reference books, notebooks, and academic stationery kits.',
    expiryDays: 45,
    stock: 'Available',
    icon: BookOpen,
  },
  {
    id: 'rew-3',
    title: '1-Week Campus Gym & Pool Access',
    category: 'gym',
    categoryLabel: 'Sports Complex',
    pointsCost: 500,
    description: 'Complimentary 7-day all-access pass to the university sports center and lap pool.',
    expiryDays: 60,
    stock: 'Available',
    icon: Dumbbell,
  },
  {
    id: 'rew-4',
    title: 'Priority Quiet Study Pod (2 Hours)',
    category: 'wellness',
    categoryLabel: 'Main Library',
    pointsCost: 250,
    description: 'Guaranteed acoustic study pod reservation with ergonomic seating.',
    expiryDays: 20,
    stock: 'Limited slots daily',
    icon: Clock,
  },
  {
    id: 'rew-5',
    title: 'Campus Mindfulness Workshop Pass',
    category: 'wellness',
    categoryLabel: 'Student Wellbeing Centre',
    pointsCost: 400,
    description: 'Admit-one ticket to the weekend sound bath and guided meditation retreat.',
    expiryDays: 45,
    stock: '12 passes left',
    icon: Sparkles,
  },
]

interface ClaimedVoucher {
  id: string
  title: string
  pointsPaid: number
  code: string
  claimedDate: string
  expiresDate: string
  location: string
}

export function StudentLeaderboardRewardsPage({
  demoMode,
}: StudentLeaderboardRewardsPageProps) {
  const [activeTab, setActiveTab] = useState<'leaderboard' | 'rewards' | 'claimed'>('leaderboard')
  const [userPoints, setUserPoints] = useState(850)
  const [isAnonymous, setIsAnonymous] = useState(false)
  const [copiedCode, setCopiedCode] = useState<string | null>(null)
  const [claimedVouchers, setClaimedVouchers] = useState<ClaimedVoucher[]>([
    {
      id: 'claim-1',
      title: 'Free Artisanal Coffee / Beverage',
      pointsPaid: 150,
      code: 'DISHA-CAFE-7492',
      claimedDate: '26 Oct 2026',
      expiresDate: '26 Nov 2026',
      location: 'Campus Central Cafe (Student Union)',
    },
  ])

  // Reward redemption modal state
  const [selectedReward, setSelectedReward] = useState<RewardItem | null>(null)
  const [showConfirmModal, setShowConfirmModal] = useState(false)

  const handleRedeemClick = (reward: RewardItem) => {
    setSelectedReward(reward)
    setShowConfirmModal(true)
  }

  const handleConfirmRedemption = () => {
    if (!selectedReward) return
    if (userPoints < selectedReward.pointsCost) {
      alert('Not enough points to redeem this voucher.')
      return
    }

    // Deduct points
    setUserPoints((prev) => prev - selectedReward.pointsCost)

    // Generate unique code
    const randomCode = `DISHA-${selectedReward.category.toUpperCase()}-${Math.floor(
      1000 + Math.random() * 9000
    )}`

    const newClaim: ClaimedVoucher = {
      id: `claim-${Date.now()}`,
      title: selectedReward.title,
      pointsPaid: selectedReward.pointsCost,
      code: randomCode,
      claimedDate: 'Today',
      expiresDate: 'Valid for 30 days',
      location: selectedReward.categoryLabel,
    }

    setClaimedVouchers((prev) => [newClaim, ...prev])
    setShowConfirmModal(false)
    setActiveTab('claimed')
  }

  const handleCopyCode = (code: string) => {
    navigator.clipboard?.writeText(code)
    setCopiedCode(code)
    setTimeout(() => setCopiedCode(null), 2000)
  }

  return (
    <div className="flex-1 flex flex-col gap-5 font-sans select-none pb-8">
      {/* 1. TOP SUMMARY RIBBON */}
      <div className="rounded-3xl bg-gradient-to-br from-[#EDE8FB] via-[#F3EDFC] to-[#FCEEF5] p-6 border border-[#DDD6FE]/70 shadow-2xs flex flex-col md:flex-row items-center justify-between gap-6">
        {/* Left: Points & Streak */}
        <div className="flex flex-col sm:flex-row items-center sm:items-start gap-5 text-center sm:text-left">
          {/* Points Pill */}
          <div className="w-24 h-24 rounded-2xl bg-white shadow-xs border border-purple-100 flex flex-col items-center justify-center shrink-0">
            <span className="text-2xl font-black text-[#1E2433]">{userPoints}</span>
            <span className="text-[10px] font-bold text-purple-700 uppercase tracking-wider">
              Points
            </span>
          </div>

          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/80 border border-purple-200 text-purple-800 text-[11px] font-bold mb-2">
              <Trophy className="w-3.5 h-3.5 text-amber-500" />
              <span>Level 3 • Wellbeing Champion</span>
            </div>

            <h2 className="text-xl sm:text-2xl font-extrabold text-[#1E2433] tracking-tight">
              Asha's Wellbeing Rewards
            </h2>
            <p className="text-xs text-[#475569] font-medium mt-1 leading-relaxed">
              Earn points with weekly check-ins, mindful breathing, and support engagements.
            </p>

            {/* Streak indicator & Progress to next level */}
            <div className="flex items-center gap-4 mt-3">
              <div className="flex items-center gap-1.5 text-xs font-bold text-amber-800 bg-amber-100/70 px-3 py-1 rounded-full">
                <Flame className="w-3.5 h-3.5 text-amber-600 fill-amber-500" />
                <span>3-Week Streak (21 Days)</span>
              </div>
              <span className="text-[11px] text-[#64748B] font-medium">
                150 pts to Level 4
              </span>
            </div>
          </div>
        </div>

        {/* Right Badges Showcase */}
        <div className="flex flex-col gap-2 shrink-0">
          <span className="text-[11px] font-bold text-gray-500 uppercase tracking-wider text-center md:text-left">
            Earned Badges ({EARNED_BADGES.length})
          </span>
          <div className="flex items-center gap-2">
            {EARNED_BADGES.map((badge) => (
              <div
                key={badge.id}
                title={`${badge.title} • ${badge.description}`}
                className="w-10 h-10 rounded-xl bg-white shadow-2xs border border-purple-100 flex items-center justify-center text-lg hover:scale-110 transition cursor-pointer"
              >
                <span>{badge.icon}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 2. SUB-TAB NAVIGATION */}
      <div className="flex items-center justify-between border-b border-gray-200 pb-2">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('leaderboard')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
              activeTab === 'leaderboard'
                ? 'bg-[#1E2433] text-white shadow-xs'
                : 'bg-white text-gray-600 hover:text-black hover:bg-gray-50 border border-gray-200'
            }`}
          >
            <Trophy className="w-3.5 h-3.5" />
            <span>Campus Leaderboard</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('rewards')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
              activeTab === 'rewards'
                ? 'bg-[#1E2433] text-white shadow-xs'
                : 'bg-white text-gray-600 hover:text-black hover:bg-gray-50 border border-gray-200'
            }`}
          >
            <Gift className="w-3.5 h-3.5" />
            <span>Rewards Catalog</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('claimed')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
              activeTab === 'claimed'
                ? 'bg-[#1E2433] text-white shadow-xs'
                : 'bg-white text-gray-600 hover:text-black hover:bg-gray-50 border border-gray-200'
            }`}
          >
            <Ticket className="w-3.5 h-3.5" />
            <span>My Vouchers ({claimedVouchers.length})</span>
          </button>
        </div>

        {/* Anonymous privacy toggle for leaderboard */}
        {activeTab === 'leaderboard' && (
          <button
            type="button"
            onClick={() => setIsAnonymous(!isAnonymous)}
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white border border-gray-200 text-xs font-semibold text-gray-600 hover:text-black transition"
            title="Toggle anonymous presence on the public leaderboard"
          >
            {isAnonymous ? <EyeOff className="w-3.5 h-3.5 text-purple-600" /> : <Eye className="w-3.5 h-3.5 text-gray-400" />}
            <span>{isAnonymous ? 'Displaying as: Anonymous' : 'Displaying as: Asha V.'}</span>
          </button>
        )}
      </div>

      {/* 3. TAB 1: CAMPUS LEADERBOARD VIEW */}
      {activeTab === 'leaderboard' && (
        <div className="flex flex-col gap-6 animate-in fade-in duration-200">
          {/* Positive Wellbeing Culture Notice */}
          <div className="p-4 rounded-2xl bg-[#F0FDF4] border border-emerald-200 text-xs text-emerald-900 flex items-center gap-3">
            <Sparkles className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>
              <strong>Celebrating Consistency:</strong> Leaderboard points represent healthy self-care habits, check-in consistency, and stress regulation — never academic comparison or pressure.
            </span>
          </div>

          {/* Top 3 Podium Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
            {/* Rank 2 - Silver */}
            <div className="bg-white rounded-3xl p-5 border border-gray-200 shadow-2xs flex flex-col items-center text-center order-2 sm:order-1 h-64 justify-between">
              <div className="flex flex-col items-center">
                <span className="w-7 h-7 rounded-full bg-gray-100 text-gray-600 font-bold text-xs flex items-center justify-center mb-2">
                  2
                </span>
                <img
                  src={LEADERBOARD_DATA[1].avatar}
                  alt={LEADERBOARD_DATA[1].name}
                  className="w-14 h-14 rounded-full object-cover ring-2 ring-gray-300"
                />
                <h4 className="text-xs font-bold text-[#1E2433] mt-2">
                  {LEADERBOARD_DATA[1].name}
                </h4>
                <p className="text-[11px] text-gray-500">{LEADERBOARD_DATA[1].degree}</p>
              </div>

              <div className="w-full pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
                <span className="text-gray-500 font-medium">🔥 {LEADERBOARD_DATA[1].streakWeeks}w</span>
                <span className="font-extrabold text-[#1E2433]">{LEADERBOARD_DATA[1].points} pts</span>
              </div>
            </div>

            {/* Rank 1 - Gold */}
            <div className="bg-white rounded-3xl p-6 border-2 border-amber-300 shadow-md flex flex-col items-center text-center order-1 sm:order-2 h-72 justify-between relative">
              <span className="absolute -top-3 px-3 py-0.5 rounded-full bg-amber-400 text-amber-950 text-[10px] font-black uppercase tracking-wider shadow-xs">
                👑 Rank 1
              </span>

              <div className="flex flex-col items-center mt-2">
                <img
                  src={LEADERBOARD_DATA[0].avatar}
                  alt={LEADERBOARD_DATA[0].name}
                  className="w-16 h-16 rounded-full object-cover ring-4 ring-amber-300"
                />
                <h4 className="text-sm font-bold text-[#1E2433] mt-2">
                  {LEADERBOARD_DATA[0].name}
                </h4>
                <p className="text-[11px] text-gray-500">{LEADERBOARD_DATA[0].degree}</p>
              </div>

              <div className="w-full pt-3 border-t border-amber-100 flex items-center justify-between text-xs">
                <span className="text-amber-800 font-bold">🔥 {LEADERBOARD_DATA[0].streakWeeks}w streak</span>
                <span className="font-black text-amber-950 text-sm">{LEADERBOARD_DATA[0].points} pts</span>
              </div>
            </div>

            {/* Rank 3 - Bronze */}
            <div className="bg-white rounded-3xl p-5 border border-amber-100 shadow-2xs flex flex-col items-center text-center order-3 sm:order-3 h-60 justify-between">
              <div className="flex flex-col items-center">
                <span className="w-7 h-7 rounded-full bg-amber-100 text-amber-800 font-bold text-xs flex items-center justify-center mb-2">
                  3
                </span>
                <img
                  src={LEADERBOARD_DATA[2].avatar}
                  alt={LEADERBOARD_DATA[2].name}
                  className="w-14 h-14 rounded-full object-cover ring-2 ring-amber-200"
                />
                <h4 className="text-xs font-bold text-[#1E2433] mt-2">
                  {LEADERBOARD_DATA[2].name}
                </h4>
                <p className="text-[11px] text-gray-500">{LEADERBOARD_DATA[2].degree}</p>
              </div>

              <div className="w-full pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
                <span className="text-gray-500 font-medium">🔥 {LEADERBOARD_DATA[2].streakWeeks}w</span>
                <span className="font-extrabold text-[#1E2433]">{LEADERBOARD_DATA[2].points} pts</span>
              </div>
            </div>
          </div>

          {/* Full Standings List */}
          <div className="bg-white rounded-3xl p-6 border border-gray-100 shadow-2xs">
            <h3 className="text-sm font-bold text-[#1E2433] mb-4">
              All University Participants
            </h3>

            <div className="flex flex-col gap-2">
              {LEADERBOARD_DATA.map((user) => (
                <div
                  key={user.rank}
                  className={`flex items-center justify-between p-3.5 rounded-2xl border transition ${
                    user.isCurrentUser
                      ? 'bg-purple-50/70 border-purple-300 ring-2 ring-purple-200'
                      : 'border-gray-100 hover:bg-gray-50/60'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`w-7 h-7 rounded-xl flex items-center justify-center font-bold text-xs ${
                        user.rank <= 3
                          ? 'bg-amber-100 text-amber-900'
                          : user.isCurrentUser
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {user.rank}
                    </span>

                    <img
                      src={user.avatar}
                      alt={user.name}
                      className="w-9 h-9 rounded-full object-cover"
                    />

                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-[#1E2433]">
                          {user.isCurrentUser && isAnonymous ? 'Anonymous Student' : user.name}
                        </span>
                        {user.isCurrentUser && (
                          <span className="text-[10px] font-bold bg-purple-200/80 text-purple-900 px-1.5 py-0.2 rounded-md">
                            You
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-gray-400">{user.degree}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-6 text-xs">
                    <div className="flex items-center gap-1 text-gray-500 font-medium">
                      <Flame className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                      <span>{user.streakWeeks}w</span>
                    </div>

                    <div className="text-right">
                      <span className="font-extrabold text-[#1E2433] block">
                        {user.points} pts
                      </span>
                      <span className="text-[10px] text-gray-400">
                        {user.badgesCount} badges
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 4. TAB 2: REWARDS CATALOG VIEW */}
      {activeTab === 'rewards' && (
        <div className="flex flex-col gap-6 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-[#1E2433]">Available Campus Vouchers</h3>
              <p className="text-xs text-[#717E95] font-medium">
                Redeem your earned points for campus perks, dining, books, and sports facilities.
              </p>
            </div>

            <div className="text-xs font-bold bg-purple-50 text-purple-900 border border-purple-200 px-3 py-1.5 rounded-full">
              Your Balance: {userPoints} pts
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {REWARDS_CATALOG.map((item) => {
              const Icon = item.icon
              const canAfford = userPoints >= item.pointsCost

              return (
                <div
                  key={item.id}
                  className="bg-white rounded-3xl p-5 border border-gray-100 shadow-2xs flex flex-col justify-between hover:border-purple-200 transition"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center">
                        <Icon className="w-5 h-5" />
                      </div>
                      <span className="text-xs font-black text-[#1E2433] bg-purple-50 px-3 py-1 rounded-full border border-purple-100">
                        {item.pointsCost} pts
                      </span>
                    </div>

                    <span className="text-[10px] font-bold uppercase tracking-wider text-purple-600 block mb-1">
                      {item.categoryLabel}
                    </span>

                    <h4 className="text-sm font-bold text-[#1E2433] leading-snug">
                      {item.title}
                    </h4>

                    <p className="text-xs text-[#64748B] mt-1.5 leading-relaxed font-medium">
                      {item.description}
                    </p>
                  </div>

                  <div className="mt-5 pt-4 border-t border-gray-100 flex items-center justify-between">
                    <span className="text-[11px] text-gray-400 font-medium">{item.stock}</span>

                    <button
                      type="button"
                      disabled={!canAfford}
                      onClick={() => handleRedeemClick(item)}
                      className={`px-4 py-2 rounded-full text-xs font-bold transition cursor-pointer ${
                        canAfford
                          ? 'bg-[#1E2433] hover:bg-[#2C3549] text-white shadow-xs'
                          : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      }`}
                    >
                      {canAfford ? 'Redeem Voucher' : 'Need More Points'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 5. TAB 3: MY CLAIMED VOUCHERS */}
      {activeTab === 'claimed' && (
        <div className="flex flex-col gap-5 animate-in fade-in duration-200">
          <div>
            <h3 className="text-base font-bold text-[#1E2433]">My Active Vouchers</h3>
            <p className="text-xs text-[#717E95] font-medium">
              Present these redemption codes at participating campus locations.
            </p>
          </div>

          {claimedVouchers.length === 0 ? (
            <div className="bg-white rounded-3xl p-10 text-center border border-gray-100">
              <Gift className="w-10 h-10 text-gray-300 mx-auto mb-2" />
              <h4 className="text-sm font-bold text-gray-700">No vouchers claimed yet</h4>
              <p className="text-xs text-gray-400 mt-1">
                Explore the Rewards Catalog and redeem your points!
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {claimedVouchers.map((voucher) => (
                <div
                  key={voucher.id}
                  className="bg-white rounded-3xl p-5 border border-purple-100 shadow-2xs flex flex-col justify-between"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                        Active & Verified
                      </span>
                      <h4 className="text-sm font-bold text-[#1E2433] mt-2">
                        {voucher.title}
                      </h4>
                      <p className="text-xs text-gray-500 mt-0.5 font-medium">
                        📍 {voucher.location}
                      </p>
                    </div>

                    <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center shrink-0">
                      <Ticket className="w-4 h-4" />
                    </div>
                  </div>

                  {/* Code Card */}
                  <div className="mt-4 p-3 bg-gray-50 rounded-2xl border border-gray-200 flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-gray-400 font-bold uppercase block">
                        Redemption Code
                      </span>
                      <span className="text-sm font-mono font-black text-[#1E2433]">
                        {voucher.code}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleCopyCode(voucher.code)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white border border-gray-200 hover:border-purple-300 text-xs font-bold text-gray-700 transition cursor-pointer"
                    >
                      {copiedCode === voucher.code ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                          <span className="text-emerald-700">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>

                  <div className="mt-3 flex items-center justify-between text-[11px] text-gray-400">
                    <span>Claimed: {voucher.claimedDate}</span>
                    <span className="text-purple-700 font-semibold">{voucher.expiresDate}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* CONFIRMATION REDEMPTION MODAL */}
      {showConfirmModal && selectedReward && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white rounded-3xl p-6 sm:p-7 max-w-sm w-full border border-purple-100 shadow-2xl flex flex-col items-center text-center">
            <div className="w-14 h-14 rounded-2xl bg-purple-50 text-purple-700 flex items-center justify-center mb-4">
              <Gift className="w-7 h-7" />
            </div>

            <h3 className="text-lg font-bold text-[#1E2433]">Redeem Voucher?</h3>
            <p className="text-xs text-gray-600 mt-1 leading-relaxed">
              You are about to redeem <strong>{selectedReward.title}</strong> for{' '}
              <strong className="text-purple-700">{selectedReward.pointsCost} points</strong>.
            </p>

            <div className="w-full mt-4 p-3 bg-gray-50 rounded-2xl border border-gray-100 text-xs text-gray-600 flex justify-between">
              <span>Points remaining after:</span>
              <span className="font-bold text-[#1E2433]">
                {userPoints - selectedReward.pointsCost} pts
              </span>
            </div>

            <div className="flex items-center gap-3 w-full mt-6">
              <button
                type="button"
                onClick={() => setShowConfirmModal(false)}
                className="flex-1 py-2.5 rounded-full border border-gray-200 text-gray-700 text-xs font-bold hover:bg-gray-50 transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmRedemption}
                className="flex-1 py-2.5 rounded-full bg-[#1E2433] hover:bg-[#2C3549] text-white text-xs font-bold transition shadow-xs cursor-pointer"
              >
                Confirm & Redeem
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

