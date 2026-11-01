import { Course, LiveSession, ClassItem, StudentRecord, QuizQuestion, BlogPost, UserProfile } from './types'

export const INSTRUCTOR_USER: UserProfile = {
  id: 'inst-1',
  name: '',
  role: 'instructor',
  title: 'Senior Full Stack & Cloud Architect',
  email: '',
  avatar: '',
  activeStudents: 28,
  bio: 'Specializing in React, TypeScript, Cloud Infrastructure, and Microservices with 10+ years teaching experience.'
}

export const STUDENT_USER: UserProfile = {
  id: 'stud-1',
  name: '',
  role: 'student',
  title: 'Aspiring Software Developer',
  email: '',
  avatar: '',
  enrolledCoursesCount: 4,
  bio: 'Enthusiastic CS learner focused on Web Development, Cloud Computing, and AI Fundamentals.'
}


export const COUNSELLOR_USER: UserProfile = {
  id: 'couns-1',
  name: '',
  role: 'counsellor',
  title: 'Lead Student Counsellor & Wellbeing Specialist',
  email: '',
  avatar: '',
  bio: 'Specialist in student psychological wellbeing, stress regulation, and academic retention coaching.'
}

export const ADMIN_USER: UserProfile = {
  id: 'admin-1',
  name: '',
  role: 'admin',
  title: 'Dean of Student Affairs & Institutional Compliance',
  email: '',
  avatar: '',
  bio: 'Overseeing campus welfare protocols, cross-departmental interventions, and compliance audits.'
}

export const COURSES_DATA: Course[] = [
  {
    id: 'course-1',
    title: 'The Complete 2025 Full-Stack Web Development Bootcamp',
    category: 'web',
    categoryLabel: 'Computer Science & IT',
    level: 'Beginner',
    duration: '48 Hours',
    lecturesCount: 84,
    desc: 'Master HTML5, CSS3, Modern JavaScript, React 19, Node.js, Express, PostgreSQL, and deploy full-stack production apps.',
    price: '₹1,599',
    originalPrice: '₹4,999',
    rating: 4.9,
    reviewsCount: '2,345',
    badge: 'Bestseller',
    badgeColor: 'bg-[#0f9d58]',
    instructorName: 'Joseph Jackson',
    instructorTitle: 'Lead Engineering Mentor',
    instructorAvatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80',
    iconName: 'Code2',
    accentBg: 'bg-[#0f9d58]',
    modules: [
      {
        title: 'Module 1: Modern Web Foundations & Semantic HTML',
        duration: '6 hrs',
        lessons: ['HTML5 Semantic tags & accessibility', 'Box model, Flexbox and Grid deep dive', 'Responsive design for mobile & tablet']
      },
      {
        title: 'Module 2: JavaScript ES6+ and Asynchronous Programming',
        duration: '12 hrs',
        lessons: ['Arrow functions, destructuring & spread', 'Promises, Async/Await and Fetch API', 'DOM manipulation and event delegation']
      },
      {
        title: 'Module 3: React 19 Component Architecture & State',
        duration: '18 hrs',
        lessons: ['Custom hooks, Context API and useReducer', 'Tailwind CSS integration and dynamic UI', 'Performance profiling and memoization']
      },
      {
        title: 'Module 4: Backend REST APIs & Production Deployment',
        duration: '12 hrs',
        lessons: ['Express servers with middleware', 'Database schema modeling & queries', 'Vercel, Docker & CI/CD deployment']
      }
    ],
    prerequisites: ['Basic computer familiarity', 'No prior coding experience required']
  },
  {
    id: 'course-2',
    title: 'Advanced Database Management, SQL & Query Optimization',
    category: 'data',
    categoryLabel: 'Data & Analytics',
    level: 'Intermediate',
    duration: '32 Hours',
    lecturesCount: 56,
    desc: 'Design scalable relational schemas, master window functions, query execution planning, indexes, and database replication.',
    price: '₹1,599',
    originalPrice: '₹3,999',
    rating: 4.8,
    reviewsCount: '1,128',
    badge: 'High Rated',
    badgeColor: 'bg-[#1d5fd1]',
    instructorName: 'Dr. Priya Raman',
    instructorTitle: 'Principal Data Engineer',
    instructorAvatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=200&q=80',
    iconName: 'Database',
    accentBg: 'bg-[#1d5fd1]',
    modules: [
      {
        title: 'Module 1: Relational Modeling & Normalization',
        duration: '8 hrs',
        lessons: ['Entity-relationship diagrams', '1NF, 2NF, 3NF & BCNF normal forms', 'Foreign key constraints & cascading']
      },
      {
        title: 'Module 2: Complex Queries & Window Functions',
        duration: '10 hrs',
        lessons: ['Multi-table JOIN optimization', 'RANK, DENSE_RANK, LEAD and LAG', 'Common Table Expressions (CTEs)']
      },
      {
        title: 'Module 3: Query Profiling, B-Trees & Index Tuning',
        duration: '8 hrs',
        lessons: ['EXPLAIN ANALYZE deep dive', 'Composite, B-Tree and GIN indexes', 'Handling slow queries in production']
      },
      {
        title: 'Module 4: Transactions, ACID and Scalability',
        duration: '6 hrs',
        lessons: ['Locking mechanisms and deadlocks', 'Read replicas and connection pooling', 'Database backup and disaster recovery']
      }
    ],
    prerequisites: ['Basic understanding of tables and spreadsheets']
  },
  {
    id: 'course-3',
    title: 'Visual Elements of UI/UX & High-Converting Product Design',
    category: 'design',
    categoryLabel: 'Design and Multimedia',
    level: 'All Levels',
    duration: '26 Hours',
    lecturesCount: 42,
    desc: 'Master typography hierarchies, spacing grids, colour harmonies, design systems in Figma, and seamless micro-interactions.',
    price: '₹1,749',
    originalPrice: '₹4,499',
    rating: 4.9,
    reviewsCount: '987',
    badge: 'Popular',
    badgeColor: 'bg-[#0f9d58]',
    instructorName: 'Vikram Mehta',
    instructorTitle: 'Staff Product Designer',
    instructorAvatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80',
    iconName: 'Palette',
    accentBg: 'bg-[#0f9d58]',
    modules: [
      {
        title: 'Module 1: Visual Design Principles & Typography',
        duration: '6 hrs',
        lessons: ['Typographic scale and font pairings', 'Color psychology and 60-30-10 rule', 'Layout grids and white space balancing']
      },
      {
        title: 'Module 2: Figma Mastery & Reusable Component Systems',
        duration: '8 hrs',
        lessons: ['Auto-layout 5.0 and constraints', 'Component variants and design tokens', 'Interactive prototypes and micro-animations']
      },
      {
        title: 'Module 3: User Research & Usability Testing',
        duration: '6 hrs',
        lessons: ['User personas and journey mapping', 'Heuristic evaluation methods', 'Conducting remote user testing sessions']
      },
      {
        title: 'Module 4: Developer Handoff & Design Systems',
        duration: '6 hrs',
        lessons: ['Design specifications for engineers', 'Exporting assets and responsive tokens', 'Building scalable design libraries']
      }
    ],
    prerequisites: ['Curiosity for visual design; free Figma account']
  },
  {
    id: 'course-4',
    title: 'Ultimate AWS Certified Solutions Architect Program',
    category: 'cloud',
    categoryLabel: 'Computer Science & IT',
    level: 'Intermediate',
    duration: '40 Hours',
    lecturesCount: 70,
    desc: 'Design resilient, high-performing, secure AWS architectures. Cover EC2, S3, RDS, Lambda, VPC, IAM, and prepare for certification.',
    price: '₹1,599',
    originalPrice: '₹5,299',
    rating: 4.9,
    reviewsCount: '3,412',
    badge: 'Trending',
    badgeColor: 'bg-[#0d1b3e]',
    instructorName: 'Ananya Rao',
    instructorTitle: 'AWS Certified Principal Architect',
    instructorAvatar: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=200&q=80',
    iconName: 'Cloud',
    accentBg: 'bg-[#0d1b3e]',
    modules: [
      {
        title: 'Module 1: AWS Global Infrastructure & IAM Security',
        duration: '8 hrs',
        lessons: ['Regions, Availability Zones & Edge Locations', 'IAM policies, roles and MFA enforcement', 'AWS Organizations and billing alerts']
      },
      {
        title: 'Module 2: Compute & High Availability (EC2, ASG, ALB)',
        duration: '12 hrs',
        lessons: ['EC2 instance types and pricing models', 'Auto Scaling groups and health checks', 'Application Load Balancer SSL & routing']
      },
      {
        title: 'Module 3: Storage & Databases (S3, EBS, RDS, DynamoDB)',
        duration: '10 hrs',
        lessons: ['S3 lifecycle policies and replication', 'RDS Multi-AZ and Read Replicas', 'Serverless NoSQL with DynamoDB']
      },
      {
        title: 'Module 4: Networking & Security Architecture (VPC)',
        duration: '10 hrs',
        lessons: ['Custom VPC, public & private subnets', 'NAT Gateways and Network ACLs', 'Bastion hosts and VPN connections']
      }
    ],
    prerequisites: ['Basic understanding of IP networks and Linux commands']
  },
  {
    id: 'course-5',
    title: 'Business Strategy, Startup Operations & Fundraising',
    category: 'business',
    categoryLabel: 'Business and Entrepreneurship',
    level: 'Beginner',
    duration: '22 Hours',
    lecturesCount: 38,
    desc: 'Learn product-market fit validation, unit economics, pitch decks, cap tables, customer acquisition cost, and term sheets.',
    price: '₹1,499',
    originalPrice: '₹3,499',
    rating: 4.7,
    reviewsCount: '840',
    badge: 'Executive',
    badgeColor: 'bg-[#1d5fd1]',
    instructorName: 'Rohan Kapoor',
    instructorTitle: 'Founder & Angel Investor',
    instructorAvatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=200&q=80',
    iconName: 'Briefcase',
    accentBg: 'bg-[#1d5fd1]',
    modules: [
      {
        title: 'Module 1: Market Research & Problem Validation',
        duration: '5 hrs',
        lessons: ['TAM, SAM, SOM calculations', 'Customer discovery interviews', 'Validating MVP demand before code']
      },
      {
        title: 'Module 2: Financial Modeling & Unit Economics',
        duration: '6 hrs',
        lessons: ['CAC, LTV, Gross Margins and Burn Rate', 'Building a 3-statement financial forecast', 'Pricing strategies for B2B vs B2C']
      },
      {
        title: 'Module 3: Pitch Deck Design & Investor Outreach',
        duration: '6 hrs',
        lessons: ['10-slide pitch deck structure', 'Storytelling that grips venture capitalists', 'Cap table math and SAFE notes']
      },
      {
        title: 'Module 4: Scaling Customer Acquisition',
        duration: '5 hrs',
        lessons: ['Growth loops vs linear marketing channels', 'B2B enterprise sales pipeline', 'Retention and referral dynamics']
      }
    ],
    prerequisites: ['No prerequisites']
  },
  {
    id: 'course-6',
    title: 'Cybersecurity Fundamentals & Ethical Hacking Defense',
    category: 'web',
    categoryLabel: 'Computer Science & IT',
    level: 'Intermediate',
    duration: '34 Hours',
    lecturesCount: 52,
    desc: 'Understand network penetration testing, OWASP Top 10 vulnerabilities, web app firewalls, cryptography, and defensive ops.',
    price: '₹1,899',
    originalPrice: '₹4,799',
    rating: 4.8,
    reviewsCount: '1,420',
    badge: 'Popular',
    badgeColor: 'bg-[#0f9d58]',
    instructorName: 'Sarah Jenkins',
    instructorTitle: 'Certified Ethical Hacker & CISO',
    instructorAvatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=80',
    iconName: 'Lock',
    accentBg: 'bg-[#0f9d58]',
    modules: [
      {
        title: 'Module 1: Networking & Reconnaissance',
        duration: '8 hrs',
        lessons: ['TCP/IP handshakes and Wireshark inspection', 'Nmap port scanning and footprinting', 'OSINT research methodologies']
      },
      {
        title: 'Module 2: Web App Security (OWASP Top 10)',
        duration: '10 hrs',
        lessons: ['SQL Injection, XSS and CSRF exploits', 'Broken authentication and session hijacking', 'Security headers and CSP policies']
      },
      {
        title: 'Module 3: Cryptography & Secure Communications',
        duration: '8 hrs',
        lessons: ['Symmetric vs asymmetric encryption', 'TLS/SSL certificate issuance & handshake', 'Hashing algorithms and password salting']
      },
      {
        title: 'Module 4: Incident Response & Defensive Hardening',
        duration: '8 hrs',
        lessons: ['SIEM log analysis and intrusion alerts', 'Firewall rules and zero-trust policies', 'Penetration test reporting to stakeholders']
      }
    ],
    prerequisites: ['Basic Linux command line knowledge']
  }
]

export const LIVE_SESSIONS_DATA: LiveSession[] = [
  {
    id: 'live-1',
    title: 'React 19 Hooks: Real-Time Collaborative Canvas & Live Dashboard',
    instructor: 'Joseph Jackson',
    topic: 'Full-Stack Web Dev',
    timeString: 'Today · 12:30 PM IST',
    isLiveNow: true,
    viewersCount: 142,
    duration: '90 mins'
  },
  {
    id: 'live-2',
    title: 'SQL Joins & CTEs Without the Headache: Real Production Scenarios',
    instructor: 'Dr. Priya Raman',
    topic: 'Database Engineering',
    timeString: 'Tomorrow · 6:00 PM IST',
    isLiveNow: false,
    viewersCount: 88,
    duration: '60 mins'
  },
  {
    id: 'live-3',
    title: 'Figma to Code: Shipping Pixel-Perfect Responsive Micro-Interactions',
    instructor: 'Vikram Mehta',
    topic: 'UI/UX Design',
    timeString: 'Saturday · 11:00 AM IST',
    isLiveNow: false,
    viewersCount: 215,
    duration: '75 mins'
  },
  {
    id: 'live-4',
    title: 'Zero to Serverless on AWS: Deploying Microservices in 45 Minutes',
    instructor: 'Ananya Rao',
    topic: 'Cloud Computing',
    timeString: 'Sunday · 4:00 PM IST',
    isLiveNow: false,
    viewersCount: 176,
    duration: '60 mins'
  }
]

export const ACTIVE_CLASSES_DATA: ClassItem[] = [
  {
    id: 'class-1',
    name: 'CS402: Full-Stack React Architecture',
    code: 'CS402',
    instructor: 'Joseph Jackson',
    accessCode: '3mia24z9x0',
    term: 'Jun 1, 2025 - Jul 15, 2025',
    activeStudents: 28,
    createdAt: 'May 30, 2025 9:33 PM',
    subject: 'Computer Science',
    color: 'bg-blue-600'
  },
  {
    id: 'class-2',
    name: 'DB301: Advanced SQL & Query Optimizations',
    code: 'DB301',
    instructor: 'Dr. Priya Raman',
    accessCode: '8kdf71q4w2',
    term: 'Jun 10, 2025 - Jul 25, 2025',
    activeStudents: 24,
    createdAt: 'Jun 02, 2025 11:15 AM',
    subject: 'Data Systems',
    color: 'bg-emerald-600'
  },
  {
    id: 'class-3',
    name: 'UX210: Figma Prototyping & Design Systems',
    code: 'UX210',
    instructor: 'Vikram Mehta',
    accessCode: '5tzp88v1m9',
    term: 'Jun 15, 2025 - Jul 30, 2025',
    activeStudents: 31,
    createdAt: 'Jun 05, 2025 3:45 PM',
    subject: 'Design',
    color: 'bg-violet-600'
  }
]

export const STUDENTS_DATA: StudentRecord[] = [
  {
    id: 'stud-1',
    name: 'Aarav Sharma',
    email: '',
    avatar: 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=150&q=80',
    status: 'Present',
    attendanceRate: 96,
    quizScore: 92,
    lastActive: '5 mins ago'
  },
  {
    id: 'stud-2',
    name: 'Tanvi Verma',
    email: '',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80',
    status: 'Present',
    attendanceRate: 100,
    quizScore: 98,
    lastActive: 'Just now'
  },
  {
    id: 'stud-3',
    name: 'Devansh Kulkarni',
    email: '',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=150&q=80',
    status: 'Late',
    attendanceRate: 84,
    quizScore: 78,
    lastActive: '12 mins ago'
  },
  {
    id: 'stud-4',
    name: 'Meera Nambiar',
    email: '',
    avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=150&q=80',
    status: 'Present',
    attendanceRate: 92,
    quizScore: 88,
    lastActive: '1 hr ago'
  },
  {
    id: 'stud-5',
    name: 'Rohan Deshmukh',
    email: '',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=150&q=80',
    status: 'Absent',
    attendanceRate: 72,
    quizScore: 65,
    lastActive: '2 days ago'
  },
  {
    id: 'stud-6',
    name: 'Ananya Pillai',
    email: '',
    avatar: 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=150&q=80',
    status: 'Present',
    attendanceRate: 95,
    quizScore: 90,
    lastActive: '8 mins ago'
  }
]

export const QUIZ_QUESTIONS: QuizQuestion[] = [
  {
    id: 1,
    question: 'In React 19, which hook is primarily used for handling transitions without blocking UI updates?',
    options: ['useEffect()', 'useTransition()', 'useCallback()', 'useLayoutEffect()'],
    correctIndex: 1,
    explanation: 'useTransition() lets you mark state updates as non-urgent transitions, keeping the user interface snappy and responsive during heavy renders.'
  },
  {
    id: 2,
    question: 'Which SQL clause is used to filter aggregated data following a GROUP BY statement?',
    options: ['WHERE', 'ORDER BY', 'HAVING', 'LIMIT'],
    correctIndex: 2,
    explanation: 'HAVING is applied after grouping and aggregation, whereas WHERE filters individual rows before grouping occurs.'
  },
  {
    id: 3,
    question: 'In UX design, what does the 60-30-10 color rule recommend for dominant, secondary, and accent colors?',
    options: [
      '60% accent, 30% dominant, 10% neutral',
      '60% dominant base, 30% secondary structure, 10% focal accent',
      '60% dark mode, 30% gradients, 10% text',
      '60% borders, 30% background, 10% buttons'
    ],
    correctIndex: 1,
    explanation: 'The 60-30-10 rule states 60% should be the dominant neutral/base background, 30% secondary surface or structural color, and 10% bright accent for CTAs and highlights.'
  },
  {
    id: 4,
    question: 'Which AWS service provides low-latency, scalable object storage with fine-grained access control?',
    options: ['Amazon RDS', 'Amazon EBS', 'Amazon S3', 'Amazon EFS'],
    correctIndex: 2,
    explanation: 'Amazon Simple Storage Service (Amazon S3) is an industry-leading object storage service offering 99.999999999% (11 9s) of durability.'
  }
]

export const BLOG_POSTS: BlogPost[] = [
  {
    id: 'blog-1',
    title: 'How to build a developer portfolio recruiters actually open in 2025',
    excerpt: 'Three production projects, one README template, and the psychological order to showcase your work.',
    content: [
      'Recruiters look at hundreds of resumes every single week. Generic todo lists or tutorial clones no longer stand out.',
      'To capture interest in under 30 seconds, showcase 3 deep-dive projects that solve authentic business problems: an interactive SaaS dashboard, an asynchronous worker with database indexes, and a clean public API with real latency benchmarking.',
      'Highlight architecture decisions, tradeoffs you made, and write concise README files featuring dynamic GIF demos and live production URLs.'
    ],
    tag: 'Careers',
    tagBg: 'bg-[#0f9d58]',
    date: 'Apr 18, 2025',
    readTime: '5 min read',
    img: 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=600&q=80',
    author: 'Joseph Jackson'
  },
  {
    id: 'blog-2',
    title: 'Mastering SQL in 30 days: a practical hands-on roadmap',
    excerpt: 'Daily 40-minute interactive sessions taking you from basic SELECT queries to advanced window functions and query execution plans.',
    content: [
      'Data engineering and backend performance both hinge on clean, predictable SQL queries. Spending 40 focused minutes daily can transform your confidence.',
      'Week 1 focuses on relational joins and groupings. Week 2 tackles subqueries, Common Table Expressions (CTEs), and window functions like ROW_NUMBER() and LEAD().',
      'Week 3 and 4 dive into EXPLAIN ANALYZE, composite indexing, and eliminating sequential table scans in high-throughput applications.'
    ],
    tag: 'Data',
    tagBg: 'bg-[#1d5fd1]',
    date: 'Apr 09, 2025',
    readTime: '7 min read',
    img: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=600&q=80',
    author: 'Dr. Priya Raman'
  },
  {
    id: 'blog-3',
    title: 'Why collaborative study groups beat solo learning for tech careers',
    excerpt: 'What we observed across 7,000+ active learners regarding peer accountability, pair programming, and career breakthroughs.',
    content: [
      'Learning in isolation often leads to burnout and tutorial paralysis. When students review each others code and collaborate on whiteboard sessions, retention jumps by over 68%.',
      'Pair programming forces you to verbalize your thinking process, preparing you directly for technical interviews and remote team dynamics.',
      'SkillsUp live cohort sessions simulate real daily standups, giving developers the confidence to ship software in cross-functional environments.'
    ],
    tag: 'Community',
    tagBg: 'bg-[#0f9d58]',
    date: 'Mar 27, 2025',
    readTime: '4 min read',
    img: 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=600&q=80',
    author: 'Vikram Mehta'
  }
]

export const MENTORS_DATA = [
  {
    name: 'Joseph Jackson',
    role: 'Lead Engineering Mentor',
    company: 'SkillsUp Core',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80',
    coursesCount: 8,
    specialty: 'React 19 & Distributed Systems'
  },
  {
    name: 'Dr. Priya Raman',
    role: 'Principal Data Engineer',
    company: 'Ex-Amazon / FinTech',
    avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=300&q=80',
    coursesCount: 5,
    specialty: 'PostgreSQL, Spark & Query Tuning'
  },
  {
    name: 'Vikram Mehta',
    role: 'Staff Product Designer',
    company: 'Design System Lead',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=300&q=80',
    coursesCount: 6,
    specialty: 'Figma Design Tokens & Micro-Interactions'
  },
  {
    name: 'Ananya Rao',
    role: 'AWS Solutions Architect',
    company: 'Cloud Advisory',
    avatar: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=300&q=80',
    coursesCount: 7,
    specialty: 'Serverless, Kubernetes & Security'
  }
]
