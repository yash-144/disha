import React, { useState, useRef, useEffect } from 'react'
import {
  Search,
  Send,
  Paperclip,
  Smile,
  Shield,
  FileText,
  Download,
  Calendar,
  CheckCheck,
  MoreVertical,
  Circle,
  Clock,
  ExternalLink,
  ChevronRight,
  UserCheck,
} from 'lucide-react'
import { DemoMode } from './studentDemoData'

interface StudentMessagesPageProps {
  demoMode: DemoMode
  onScheduleCall?: () => void
}

interface Message {
  id: string
  sender: 'student' | 'recipient'
  text: string
  time: string
  status?: 'sent' | 'delivered' | 'read'
  attachment?: {
    name: string
    size: string
    type: 'pdf' | 'doc'
  }
}

interface Conversation {
  id: string
  name: string
  role: string
  department: string
  avatar: string
  isOnline: boolean
  lastSeen?: string
  unreadCount: number
  category: 'mentor' | 'counsellor' | 'support'
  messages: Message[]
}

const INITIAL_CONVERSATIONS: Conversation[] = [
  {
    id: 'conv-1',
    name: 'Prof. Sharma',
    role: 'Faculty Mentor & Course Instructor',
    department: 'Department of Computer Science',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80',
    isOnline: true,
    lastSeen: 'Active now',
    unreadCount: 1,
    category: 'mentor',
    messages: [
      {
        id: 'm-1',
        sender: 'recipient',
        text: 'Hi Asha, I reviewed your milestone update from yesterday. Really pleased to see your consistent lab attendance this week.',
        time: '10:45 AM',
        status: 'read',
      },
      {
        id: 'm-2',
        sender: 'student',
        text: 'Thank you Prof. Sharma! The makeup schedule helped me catch up on the Trees & Graphs module without feeling rushed.',
        time: '10:52 AM',
        status: 'read',
      },
      {
        id: 'm-3',
        sender: 'recipient',
        text: 'Glad to hear that. I signed the academic attestation and logged your Lab 3 extension agreement in DISHA. You can review the verified summary below.',
        time: '11:01 AM',
        status: 'read',
        attachment: {
          name: 'Lab3_Extension_Attestation.pdf',
          size: '142 KB',
          type: 'pdf',
        },
      },
      {
        id: 'm-4',
        sender: 'recipient',
        text: 'Let me know if you would like to schedule a quick 10-minute check-in before Thursday’s project demonstration.',
        time: '11:02 AM',
        status: 'read',
      },
    ],
  },
  {
    id: 'conv-2',
    name: 'Dr. Radhika Iyer',
    role: 'Lead Student Counsellor',
    department: 'Student Wellbeing Centre',
    avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=300&q=80',
    isOnline: false,
    lastSeen: 'Active 2h ago',
    unreadCount: 0,
    category: 'counsellor',
    messages: [
      {
        id: 'm-201',
        sender: 'recipient',
        text: 'Hello Asha! Just checking in after your wellbeing assessment. Remember that taking brief breathing pauses during study marathons works wonders.',
        time: 'Yesterday, 3:30 PM',
        status: 'read',
      },
      {
        id: 'm-202',
        sender: 'student',
        text: 'Hi Dr. Iyer, thank you for the reminder! The box breathing exercise in the portal has been really helpful.',
        time: 'Yesterday, 4:15 PM',
        status: 'read',
      },
      {
        id: 'm-203',
        sender: 'recipient',
        text: 'Wonderful! Feel free to book a confidential consultation anytime through the Request Support tab if you ever need an ear.',
        time: 'Yesterday, 4:20 PM',
        status: 'read',
      },
    ],
  },
  {
    id: 'conv-3',
    name: 'Academic Support Desk',
    role: 'Peer Tutoring & Accommodations Coordinator',
    department: 'Academic Affairs Office',
    avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=300&q=80',
    isOnline: false,
    lastSeen: 'Active yesterday',
    unreadCount: 0,
    category: 'support',
    messages: [
      {
        id: 'm-301',
        sender: 'recipient',
        text: 'Hello Asha, your reservation for the Quiet Study Pod (Pod B-4) for Tuesday 2:00 PM - 4:00 PM is confirmed.',
        time: 'Wednesday',
        status: 'read',
      },
      {
        id: 'm-302',
        sender: 'student',
        text: 'Received, thank you!',
        time: 'Wednesday',
        status: 'read',
      },
    ],
  },
]

const QUICK_SUGGESTIONS = [
  'Could we schedule a brief check-in?',
  'Thank you for the guidance!',
  'I have completed the milestone exercise.',
  'Could you review my lab extension request?',
]

export function StudentMessagesPage({
  demoMode,
  onScheduleCall,
}: StudentMessagesPageProps) {
  const [conversations, setConversations] = useState<Conversation[]>(INITIAL_CONVERSATIONS)
  const [selectedConvId, setSelectedConvId] = useState<string>('conv-1')
  const [filterCategory, setFilterCategory] = useState<'all' | 'mentor' | 'counsellor' | 'support'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [inputText, setInputText] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const activeConv =
    conversations.find((c) => c.id === selectedConvId) || conversations[0]

  const filteredConversations = conversations.filter((c) => {
    const matchesCategory = filterCategory === 'all' || c.category === filterCategory
    const matchesSearch =
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.role.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesCategory && matchesSearch
  })

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activeConv.messages])

  // Mark unread as read when clicking conversation
  const handleSelectConversation = (id: string) => {
    setSelectedConvId(id)
    setConversations((prev) =>
      prev.map((c) => (c.id === id ? { ...c, unreadCount: 0 } : c))
    )
  }

  // Send message
  const handleSendMessage = (textToSend?: string) => {
    const text = (textToSend || inputText).trim()
    if (!text) return

    const newMsg: Message = {
      id: `m-${Date.now()}`,
      sender: 'student',
      text,
      time: 'Just now',
      status: 'sent',
    }

    setConversations((prev) =>
      prev.map((c) => {
        if (c.id === selectedConvId) {
          return {
            ...c,
            messages: [...c.messages, newMsg],
          }
        }
        return c
      })
    )

    setInputText('')

    // Simulate supportive automated acknowledgement after 1.5 seconds
    setTimeout(() => {
      const replyMsg: Message = {
        id: `m-reply-${Date.now()}`,
        sender: 'recipient',
        text: 'Thank you for updating me, Asha. I have noted this in your support file and will follow up shortly!',
        time: 'Just now',
        status: 'delivered',
      }

      setConversations((prev) =>
        prev.map((c) => {
          if (c.id === selectedConvId) {
            return {
              ...c,
              messages: [...c.messages, replyMsg],
            }
          }
          return c
        })
      )
    }, 1500)
  }

  return (
    <div className="flex-1 flex flex-col font-sans select-none pb-4">
      {/* Messaging Container Surface */}
      <div className="bg-white rounded-3xl border border-gray-100 shadow-2xs overflow-hidden flex flex-col md:flex-row h-[720px]">
        {/* LEFT INBOX PANE */}
        <aside className="w-full md:w-80 shrink-0 border-r border-gray-100 flex flex-col bg-[#FAFBFD]">
          {/* Top Search & Filter */}
          <div className="p-4 border-b border-gray-100 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-[#1E2433]">Inbox</h2>
              <span className="text-[11px] font-semibold text-purple-700 bg-purple-50 px-2.5 py-0.5 rounded-full">
                {conversations.reduce((sum, c) => sum + c.unreadCount, 0)} new
              </span>
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search messages & contacts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 bg-white border border-gray-200 rounded-xl text-xs text-[#1E2433] placeholder-gray-400 focus:outline-none focus:border-purple-400 shadow-2xs"
              />
            </div>

            {/* Filter Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-[11px] font-semibold">
              <button
                type="button"
                onClick={() => setFilterCategory('all')}
                className={`px-2.5 py-1 rounded-lg transition shrink-0 ${
                  filterCategory === 'all'
                    ? 'bg-[#1E2433] text-white'
                    : 'bg-white border border-gray-200 text-[#64748B] hover:text-[#1E2433]'
                }`}
              >
                All
              </button>
              <button
                type="button"
                onClick={() => setFilterCategory('mentor')}
                className={`px-2.5 py-1 rounded-lg transition shrink-0 ${
                  filterCategory === 'mentor'
                    ? 'bg-purple-600 text-white'
                    : 'bg-white border border-gray-200 text-[#64748B] hover:text-[#1E2433]'
                }`}
              >
                Mentors
              </button>
              <button
                type="button"
                onClick={() => setFilterCategory('counsellor')}
                className={`px-2.5 py-1 rounded-lg transition shrink-0 ${
                  filterCategory === 'counsellor'
                    ? 'bg-rose-600 text-white'
                    : 'bg-white border border-gray-200 text-[#64748B] hover:text-[#1E2433]'
                }`}
              >
                Counsellors
              </button>
              <button
                type="button"
                onClick={() => setFilterCategory('support')}
                className={`px-2.5 py-1 rounded-lg transition shrink-0 ${
                  filterCategory === 'support'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-200 text-[#64748B] hover:text-[#1E2433]'
                }`}
              >
                Support Desk
              </button>
            </div>
          </div>

          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto divide-y divide-gray-50 p-2">
            {filteredConversations.map((conv) => {
              const isSelected = conv.id === selectedConvId
              const lastMsg = conv.messages[conv.messages.length - 1]

              return (
                <button
                  key={conv.id}
                  type="button"
                  onClick={() => handleSelectConversation(conv.id)}
                  className={`w-full flex items-start gap-3 p-3 rounded-2xl text-left transition cursor-pointer mb-1 ${
                    isSelected
                      ? 'bg-white shadow-2xs border border-purple-100 ring-1 ring-purple-100'
                      : 'hover:bg-white/80'
                  }`}
                >
                  {/* Avatar + Online Indicator */}
                  <div className="relative shrink-0">
                    <img
                      src={conv.avatar}
                      alt={conv.name}
                      className="w-10 h-10 rounded-full object-cover shadow-2xs border border-white"
                    />
                    {conv.isOnline && (
                      <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-500 ring-2 ring-white rounded-full" />
                    )}
                  </div>

                  {/* Info & Snippet */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-0.5">
                      <h3
                        className={`text-xs font-bold truncate ${
                          isSelected ? 'text-[#1E2433]' : 'text-gray-800'
                        }`}
                      >
                        {conv.name}
                      </h3>
                      <span className="text-[10px] text-gray-400 font-medium shrink-0 ml-1">
                        {lastMsg ? lastMsg.time : ''}
                      </span>
                    </div>

                    <p className="text-[11px] text-[#64748B] font-medium truncate mb-1">
                      {conv.role}
                    </p>

                    <p className="text-[11px] text-gray-500 truncate leading-snug">
                      {lastMsg ? lastMsg.text : 'No messages yet.'}
                    </p>
                  </div>

                  {/* Unread badge */}
                  {conv.unreadCount > 0 && (
                    <span className="w-2 h-2 rounded-full bg-purple-600 shrink-0 self-center" />
                  )}
                </button>
              )
            })}
          </div>
        </aside>

        {/* RIGHT ACTIVE CHAT PANE */}
        <div className="flex-1 flex flex-col bg-white">
          {/* Chat Header */}
          <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-white z-10">
            <div className="flex items-center gap-3">
              <div className="relative">
                <img
                  src={activeConv.avatar}
                  alt={activeConv.name}
                  className="w-10 h-10 rounded-full object-cover ring-2 ring-purple-50 shadow-2xs"
                />
                {activeConv.isOnline && (
                  <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-500 ring-2 ring-white rounded-full" />
                )}
              </div>
              <div>
                <h3 className="text-sm font-bold text-[#1E2433] leading-tight">
                  {activeConv.name}
                </h3>
                <p className="text-[11px] text-[#64748B] font-medium mt-0.5">
                  {activeConv.role} •{' '}
                  <span className="text-emerald-600 font-semibold">{activeConv.lastSeen}</span>
                </p>
              </div>
            </div>

            {/* Quick Action Button */}
            <div className="flex items-center gap-2">
              {onScheduleCall && (
                <button
                  type="button"
                  onClick={onScheduleCall}
                  className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-purple-50 hover:bg-purple-100 text-purple-700 text-xs font-bold border border-purple-200 transition"
                >
                  <Calendar className="w-3.5 h-3.5" />
                  <span>Request Session</span>
                </button>
              )}
            </div>
          </div>

          {/* Privacy & Confidentiality Notice Banner */}
          <div className="px-4 py-2 bg-[#F8FAFC] border-b border-gray-100 flex items-center gap-2 text-[11px] text-[#64748B] font-medium">
            <Shield className="w-3.5 h-3.5 text-purple-600 shrink-0" />
            <span>
              <strong>Confidentiality Protected:</strong> Messages between students and appointed mentors are private and stored with immutable integrity in accordance with university welfare policies.
            </span>
          </div>

          {/* Message Thread Body */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-5 flex flex-col gap-3.5 bg-[#FAFBFD]/40">
            {/* Timestamp Divider */}
            <div className="flex items-center justify-center my-1">
              <span className="text-[10px] text-gray-400 bg-white border border-gray-200 px-3 py-0.5 rounded-full font-medium">
                Today
              </span>
            </div>

            {activeConv.messages.map((msg) => {
              const isStudent = msg.sender === 'student'

              return (
                <div
                  key={msg.id}
                  className={`flex items-end gap-2 max-w-[85%] sm:max-w-[75%] ${
                    isStudent ? 'self-end flex-row-reverse' : 'self-start'
                  }`}
                >
                  {/* Recipient avatar for incoming messages */}
                  {!isStudent && (
                    <img
                      src={activeConv.avatar}
                      alt={activeConv.name}
                      className="w-7 h-7 rounded-full object-cover shrink-0 mb-1"
                    />
                  )}

                  <div className="flex flex-col gap-1">
                    {/* Message Bubble */}
                    <div
                      className={`p-3.5 rounded-2xl text-xs leading-relaxed ${
                        isStudent
                          ? 'bg-[#1E2433] text-white rounded-br-xs shadow-xs'
                          : 'bg-white border border-gray-200 text-[#1E2433] rounded-bl-xs shadow-2xs'
                      }`}
                    >
                      <p>{msg.text}</p>

                      {/* Attachment preview if present */}
                      {msg.attachment && (
                        <div
                          className={`mt-2.5 p-2.5 rounded-xl border flex items-center justify-between gap-3 ${
                            isStudent
                              ? 'bg-white/10 border-white/20 text-white'
                              : 'bg-purple-50/70 border-purple-100 text-[#1E2433]'
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <div className="w-7 h-7 rounded-lg bg-red-100 text-red-600 flex items-center justify-center shrink-0">
                              <FileText className="w-3.5 h-3.5" />
                            </div>
                            <div className="truncate">
                              <p className="text-[11px] font-bold truncate">
                                {msg.attachment.name}
                              </p>
                              <span className="text-[10px] opacity-70">
                                {msg.attachment.size} • Cryptographically Signed
                              </span>
                            </div>
                          </div>

                          <button
                            type="button"
                            className="p-1 rounded-lg hover:bg-black/10 transition shrink-0 cursor-pointer"
                            title="Download verified document"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Time & Read receipts */}
                    <div
                      className={`flex items-center gap-1 text-[10px] text-gray-400 px-1 ${
                        isStudent ? 'self-end' : 'self-start'
                      }`}
                    >
                      <span>{msg.time}</span>
                      {isStudent && <CheckCheck className="w-3 h-3 text-purple-500" />}
                    </div>
                  </div>
                </div>
              )
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Suggestions Chips */}
          <div className="px-4 py-2 bg-white border-t border-gray-100 flex items-center gap-2 overflow-x-auto text-[11px]">
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider shrink-0">
              Quick:
            </span>
            {QUICK_SUGGESTIONS.map((text, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSendMessage(text)}
                className="px-3 py-1 rounded-full bg-gray-50 hover:bg-purple-50 hover:text-purple-700 border border-gray-200 hover:border-purple-200 text-gray-600 transition shrink-0 cursor-pointer"
              >
                {text}
              </button>
            ))}
          </div>

          {/* Message Input Composer */}
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSendMessage()
            }}
            className="p-3 sm:p-4 border-t border-gray-100 bg-white flex items-center gap-2"
          >
            <button
              type="button"
              className="p-2 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-full transition cursor-pointer"
              title="Attach Document or Attestation"
            >
              <Paperclip className="w-4 h-4" />
            </button>

            <input
              type="text"
              placeholder={`Message ${activeConv.name}...`}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="flex-1 px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-full text-xs text-[#1E2433] placeholder-gray-400 focus:outline-none focus:border-purple-400 focus:bg-white transition"
            />

            <button
              type="submit"
              disabled={!inputText.trim()}
              className={`p-2.5 rounded-full transition cursor-pointer ${
                inputText.trim()
                  ? 'bg-[#1E2433] hover:bg-[#2C3549] text-white shadow-xs'
                  : 'bg-gray-100 text-gray-300 cursor-not-allowed'
              }`}
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

