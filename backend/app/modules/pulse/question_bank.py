"""Student Pulse Question Bank and Seed Data.

Contains realistic questions across three categories:
- Category A: Academic Assessment (MCQ & Descriptive with difficulty, marks, keys, explanations)
- Category B: Classroom Feedback (Likert scales, pace, engagement, anonymized)
- Category C: Student Wellbeing (Motivation, pressure, exam confidence, non-diagnostic)
"""

COURSE_QUESTION_BANK = [
    # =========================================================================
    # COURSE 1: CS201 - Data Structures & Algorithms
    # =========================================================================
    
    # --- Category A: Academic Assessment ---
    {
        "id": "cs201-acad-01",
        "course_id": "CS201",
        "course_name": "Data Structures & Algorithms",
        "category": "ACADEMIC",
        "prompt": "Which data structure follows the Last-In-First-Out (LIFO) principle and is commonly used for function call stacks?",
        "question_type": "mcq",
        "difficulty": "Easy",
        "marks": 2.0,
        "options": [
            "Queue",
            "Stack",
            "Binary Search Tree",
            "Doubly Linked List"
        ],
        "correct_option": 1,
        "correct_answer": "Stack",
        "explanation": "A Stack follows the Last-In-First-Out (LIFO) discipline, making it the canonical structure for recursion and call stack management.",
        "parameter_tag": "stack-basics"
    },
    {
        "id": "cs201-acad-02",
        "course_id": "CS201",
        "course_name": "Data Structures & Algorithms",
        "category": "ACADEMIC",
        "prompt": "What is the worst-case time complexity of searching for an element in an unbalanced Binary Search Tree (BST) containing n nodes?",
        "question_type": "mcq",
        "difficulty": "Medium",
        "marks": 3.0,
        "options": [
            "O(1)",
            "O(log n)",
            "O(n)",
            "O(n log n)"
        ],
        "correct_option": 2,
        "correct_answer": "O(n)",
        "explanation": "When a BST becomes completely skewed (degenerate tree resembling a linked list), searching deteriorates to linear time O(n).",
        "parameter_tag": "bst-complexity"
    },
    {
        "id": "cs201-acad-03",
        "course_id": "CS201",
        "course_name": "Data Structures & Algorithms",
        "category": "ACADEMIC",
        "prompt": "In recursion, what occurs if the base case is omitted or incorrectly defined?",
        "question_type": "mcq",
        "difficulty": "Easy",
        "marks": 2.0,
        "options": [
            "Compilation error during build",
            "Stack overflow due to infinite recursive calls",
            "Memory leak in the heap space",
            "Program executes in O(1) constant time"
        ],
        "correct_option": 1,
        "correct_answer": "Stack overflow due to infinite recursive calls",
        "explanation": "Without a base case termination condition, recursive calls continue allocating stack frames until the execution stack exhausts memory, triggering a stack overflow.",
        "parameter_tag": "recursion-fundamentals"
    },
    {
        "id": "cs201-acad-04",
        "course_id": "CS201",
        "course_name": "Data Structures & Algorithms",
        "category": "ACADEMIC",
        "prompt": "Which tree traversal strategy visits the Left subtree, the Root node, and then the Right subtree?",
        "question_type": "mcq",
        "difficulty": "Easy",
        "marks": 2.0,
        "options": [
            "Pre-order Traversal",
            "In-order Traversal",
            "Post-order Traversal",
            "Level-order Traversal"
        ],
        "correct_option": 1,
        "correct_answer": "In-order Traversal",
        "explanation": "In-order traversal visits nodes in the sequence (Left, Root, Right), which outputs sorted elements in a Binary Search Tree.",
        "parameter_tag": "tree-traversal"
    },
    {
        "id": "cs201-acad-05",
        "course_id": "CS201",
        "course_name": "Data Structures & Algorithms",
        "category": "ACADEMIC",
        "prompt": "Explain the difference between a Graph Depth-First Search (DFS) and Breadth-First Search (BFS) in terms of auxiliary data structure and traversal behavior.",
        "question_type": "descriptive",
        "difficulty": "Medium",
        "marks": 5.0,
        "options": [],
        "correct_option": None,
        "correct_answer": "DFS uses a Stack (or call stack) exploring depth-first along each branch; BFS uses a Queue exploring vertex-by-vertex layer by layer.",
        "explanation": "Key rubric points: Mentioning Stack vs Queue, depth exploration vs level-order exploration, and handling visited sets to avoid cycles.",
        "parameter_tag": "graph-traversal"
    },
    {
        "id": "cs201-acad-06",
        "course_id": "CS201",
        "course_name": "Data Structures & Algorithms",
        "category": "ACADEMIC",
        "prompt": "Given an array of size n, which sorting algorithm achieves an average time complexity of O(n log n) while operating in-place with O(1) extra space?",
        "question_type": "mcq",
        "difficulty": "Hard",
        "marks": 3.0,
        "options": [
            "Merge Sort",
            "Heap Sort",
            "Counting Sort",
            "Radix Sort"
        ],
        "correct_option": 1,
        "correct_answer": "Heap Sort",
        "explanation": "Heap Sort sorts in-place using an implicit heap structure inside the array with O(n log n) worst and average case, requiring only O(1) auxiliary space.",
        "parameter_tag": "sorting-efficiency"
    },
    {
        "id": "cs201-acad-07",
        "course_id": "CS201",
        "course_name": "Data Structures & Algorithms",
        "category": "ACADEMIC",
        "prompt": "What data structure is optimal for implementing a Priority Queue with logarithmic insertion and deletion times?",
        "question_type": "mcq",
        "difficulty": "Medium",
        "marks": 3.0,
        "options": [
            "Binary Heap",
            "Sorted Circular Array",
            "Hash Table with Chaining",
            "Singly Linked List"
        ],
        "correct_option": 0,
        "correct_answer": "Binary Heap",
        "explanation": "A Binary Heap (Min-Heap or Max-Heap) guarantees O(log n) insertion and extraction of the minimum/maximum element.",
        "parameter_tag": "priority-queues"
    },

    # --- Category B: Classroom Feedback ---
    {
        "id": "cs201-feed-01",
        "course_id": "CS201",
        "course_name": "Data Structures & Algorithms",
        "category": "CLASSROOM_FEEDBACK",
        "prompt": "How would you rate the lecture pace during recent data structures lectures?",
        "question_type": "single_choice",
        "difficulty": "Easy",
        "marks": 0.0,
        "options": [
            "Too fast – hard to keep up with code implementations",
            "Just right – manageable pace with clear progression",
            "Too slow – concepts could be covered more efficiently"
        ],
        "correct_option": None,
        "correct_answer": None,
        "explanation": "Helps faculty calibrate teaching velocity.",
        "parameter_tag": "lecture_pace"
    },
    {
        "id": "cs201-feed-02",
        "course_id": "CS201",
        "course_name": "Data Structures & Algorithms",
        "category": "CLASSROOM_FEEDBACK",
        "prompt": "Clarity of algorithmic proofs and dry runs on the whiteboard / slides:",
        "question_type": "likert",
        "difficulty": "Easy",
        "marks": 0.0,
        "options": [
            "1 - Very Unclear",
            "2 - Needs More Examples",
            "3 - Moderately Clear",
            "4 - Clear & Structured",
            "5 - Exceptionally Lucid"
        ],
        "correct_option": None,
        "correct_answer": None,
        "explanation": "Evaluates blackboard/visual trace efficacy.",
        "parameter_tag": "clarity_explanation"
    },
    {
        "id": "cs201-feed-03",
        "course_id": "CS201",
        "course_name": "Data Structures & Algorithms",
        "category": "CLASSROOM_FEEDBACK",
        "prompt": "How comfortable do you feel asking questions or seeking clarification during class?",
        "question_type": "single_choice",
        "difficulty": "Easy",
        "marks": 0.0,
        "options": [
            "Comfortable asking questions immediately during lecture",
            "Prefer asking after class or during office hours",
            "Somewhat hesitant to speak up in front of the whole batch",
            "Prefer submitting questions anonymously or online"
        ],
        "correct_option": None,
        "correct_answer": None,
        "explanation": "Gauges psychological safety in classroom discussions.",
        "parameter_tag": "asking_questions"
    },
    {
        "id": "cs201-feed-04",
        "course_id": "CS201",
        "course_name": "Data Structures & Algorithms",
        "category": "CLASSROOM_FEEDBACK",
        "prompt": "Adequacy of practical hands-on coding demonstrations during sessions:",
        "question_type": "likert",
        "difficulty": "Easy",
        "marks": 0.0,
        "options": [
            "1 - Strongly Insufficient",
            "2 - Below Average",
            "3 - Adequate",
            "4 - Good Practical Balance",
            "5 - Excellent Hands-on Depth"
        ],
        "correct_option": None,
        "correct_answer": None,
        "explanation": "Assesses balance between theory and live coding exercises.",
        "parameter_tag": "practical_exposure"
    },
    {
        "id": "cs201-feed-05",
        "course_id": "CS201",
        "course_name": "Data Structures & Algorithms",
        "category": "CLASSROOM_FEEDBACK",
        "prompt": "Which topics would you most like a dedicated revision or lab walkthrough for?",
        "question_type": "multi_choice",
        "difficulty": "Easy",
        "marks": 0.0,
        "options": [
            "Recursion & Backtracking trees",
            "Binary Search Trees & Balancing (AVL)",
            "Graph DFS/BFS & Shortest Path",
            "Dynamic Programming memoization patterns"
        ],
        "correct_option": None,
        "correct_answer": None,
        "explanation": "Direct indicator for targeted revision clinics.",
        "parameter_tag": "revision_needs"
    },

    # --- Category C: Student Wellbeing ---
    {
        "id": "cs201-well-01",
        "course_id": "CS201",
        "course_name": "Data Structures & Algorithms",
        "category": "WELLBEING",
        "prompt": "How would you rate your motivation and curiosity to learn the algorithms and topics in this course?",
        "question_type": "likert",
        "difficulty": "Easy",
        "marks": 0.0,
        "options": [
            "1 - Very Low / Drained",
            "2 - Low Motivation",
            "3 - Moderate / Managing",
            "4 - High Enthusiasm",
            "5 - Peak Motivation & Curiosity"
        ],
        "correct_option": None,
        "correct_answer": None,
        "explanation": "Academic engagement & curiosity indicator.",
        "parameter_tag": "course_motivation"
    },
    {
        "id": "cs201-well-02",
        "course_id": "CS201",
        "course_name": "Data Structures & Algorithms",
        "category": "WELLBEING",
        "prompt": "How manageable is your current academic workload and lab deadlines across your enrolled courses?",
        "question_type": "likert",
        "difficulty": "Easy",
        "marks": 0.0,
        "options": [
            "1 - Overwhelming pressure",
            "2 - Heavy strain / behind schedule",
            "3 - Manageable with regular effort",
            "4 - Well balanced and organized",
            "5 - Highly comfortable workload"
        ],
        "correct_option": None,
        "correct_answer": None,
        "explanation": "Perceived workload and burnout buffer.",
        "parameter_tag": "academic_pressure"
    },
    {
        "id": "cs201-well-03",
        "course_id": "CS201",
        "course_name": "Data Structures & Algorithms",
        "category": "WELLBEING",
        "prompt": "How confident do you feel about your preparation and conceptual readiness for the upcoming mid-term exam?",
        "question_type": "likert",
        "difficulty": "Easy",
        "marks": 0.0,
        "options": [
            "1 - Extremely anxious / unprepared",
            "2 - Uncertain on several topics",
            "3 - Moderately prepared",
            "4 - Confident in core concepts",
            "5 - Thoroughly prepared and confident"
        ],
        "correct_option": None,
        "correct_answer": None,
        "explanation": "Exam preparedness and confidence measure.",
        "parameter_tag": "exam_confidence"
    },
    {
        "id": "cs201-well-04",
        "course_id": "CS201",
        "course_name": "Data Structures & Algorithms",
        "category": "WELLBEING",
        "prompt": "Would you benefit from additional peer study circles or mentor problem-solving clinics?",
        "question_type": "single_choice",
        "difficulty": "Easy",
        "marks": 0.0,
        "options": [
            "No, I am tracking fine independently",
            "Yes, a collaborative peer study group would be beneficial",
            "Yes, an instructor-led problem solving session would help greatly",
            "Yes, I would appreciate 1-on-1 mentor guidance"
        ],
        "correct_option": None,
        "correct_answer": None,
        "explanation": "Direct signal for academic support interventions.",
        "parameter_tag": "support_readiness"
    },

    # =========================================================================
    # COURSE 2: CS202 - Database Management Systems
    # =========================================================================
    
    # --- Category A: Academic Assessment ---
    {
        "id": "cs202-acad-01",
        "course_id": "CS202",
        "course_name": "Database Management Systems",
        "category": "ACADEMIC",
        "prompt": "Which normal form eliminates partial functional dependencies on a composite candidate key?",
        "question_type": "mcq",
        "difficulty": "Medium",
        "marks": 3.0,
        "options": [
            "First Normal Form (1NF)",
            "Second Normal Form (2NF)",
            "Third Normal Form (3NF)",
            "Boyce-Codd Normal Form (BCNF)"
        ],
        "correct_option": 1,
        "correct_answer": "Second Normal Form (2NF)",
        "explanation": "2NF requires that the relation is in 1NF and no non-prime attribute is functionally dependent on a proper subset of any candidate key.",
        "parameter_tag": "normalization"
    },
    {
        "id": "cs202-acad-02",
        "course_id": "CS202",
        "course_name": "Database Management Systems",
        "category": "ACADEMIC",
        "prompt": "In ACID transaction properties, which property ensures that once a transaction commits, its modifications persist even across system crashes?",
        "question_type": "mcq",
        "difficulty": "Easy",
        "marks": 2.0,
        "options": [
            "Atomicity",
            "Consistency",
            "Isolation",
            "Durability"
        ],
        "correct_option": 3,
        "correct_answer": "Durability",
        "explanation": "Durability guarantees that committed database updates survive crashes via write-ahead logging (WAL) and disk persistence.",
        "parameter_tag": "acid-properties"
    },
    {
        "id": "cs202-acad-03",
        "course_id": "CS202",
        "course_name": "Database Management Systems",
        "category": "ACADEMIC",
        "prompt": "Which SQL clause is used to filter aggregated group records produced by a GROUP BY clause?",
        "question_type": "mcq",
        "difficulty": "Easy",
        "marks": 2.0,
        "options": [
            "WHERE",
            "HAVING",
            "ORDER BY",
            "QUALIFY"
        ],
        "correct_option": 1,
        "correct_answer": "HAVING",
        "explanation": "WHERE filters rows before aggregation; HAVING filters groups after aggregate calculation.",
        "parameter_tag": "sql-syntax"
    },
    {
        "id": "cs202-acad-04",
        "course_id": "CS202",
        "course_name": "Database Management Systems",
        "category": "ACADEMIC",
        "prompt": "Explain the difference between a Clustered Index and a Non-Clustered Index in relational databases.",
        "question_type": "descriptive",
        "difficulty": "Medium",
        "marks": 5.0,
        "options": [],
        "correct_option": None,
        "correct_answer": "A clustered index physically sorts and stores data rows in disk order (only 1 per table); a non-clustered index stores index pointers pointing to table rows.",
        "explanation": "Key rubric points: Physical row ordering vs pointer structure, single clustered index limitation vs multiple non-clustered indexes.",
        "parameter_tag": "indexing"
    },
    {
        "id": "cs202-acad-05",
        "course_id": "CS202",
        "course_name": "Database Management Systems",
        "category": "ACADEMIC",
        "prompt": "What concurrency anomaly occurs when one transaction reads uncommitted changes written by another concurrent transaction that later aborts?",
        "question_type": "mcq",
        "difficulty": "Hard",
        "marks": 3.0,
        "options": [
            "Dirty Read (Uncommitted Dependency)",
            "Non-Repeatable Read",
            "Phantom Read",
            "Lost Update"
        ],
        "correct_option": 0,
        "correct_answer": "Dirty Read (Uncommitted Dependency)",
        "explanation": "A Dirty Read happens when transaction T1 reads data modified by transaction T2 before T2 commits; if T2 rolls back, T1 processed invalid state.",
        "parameter_tag": "concurrency-control"
    },

    # --- Category B: Classroom Feedback ---
    {
        "id": "cs202-feed-01",
        "course_id": "CS202",
        "course_name": "Database Management Systems",
        "category": "CLASSROOM_FEEDBACK",
        "prompt": "How understandable was the SQL query optimization and indexing lecture?",
        "question_type": "likert",
        "difficulty": "Easy",
        "marks": 0.0,
        "options": [
            "1 - Hard to grasp",
            "2 - Moderately difficult",
            "3 - Understandable",
            "4 - Very clear",
            "5 - Crystal clear with query plan examples"
        ],
        "correct_option": None,
        "correct_answer": None,
        "explanation": "Gauges clarity on database query optimization.",
        "parameter_tag": "clarity_explanation"
    },
    {
        "id": "cs202-feed-02",
        "course_id": "CS202",
        "course_name": "Database Management Systems",
        "category": "CLASSROOM_FEEDBACK",
        "prompt": "Rate the lecture pace during SQL query and relational algebra demonstrations:",
        "question_type": "single_choice",
        "difficulty": "Easy",
        "marks": 0.0,
        "options": [
            "Too fast – need more time on complex queries",
            "Just right – well-paced with step-by-step breakdowns",
            "Too slow – would prefer advanced indexing sooner"
        ],
        "correct_option": None,
        "correct_answer": None,
        "explanation": "Pace calibration for DBMS.",
        "parameter_tag": "lecture_pace"
    },

    # --- Category C: Student Wellbeing ---
    {
        "id": "cs202-well-01",
        "course_id": "CS202",
        "course_name": "Database Management Systems",
        "category": "WELLBEING",
        "prompt": "How confident do you feel about writing SQL queries under timed examination conditions?",
        "question_type": "likert",
        "difficulty": "Easy",
        "marks": 0.0,
        "options": [
            "1 - Very stressed & nervous",
            "2 - Lacking speed and practice",
            "3 - Moderately comfortable",
            "4 - Confident in my syntax and logic",
            "5 - Highly fluent and confident"
        ],
        "correct_option": None,
        "correct_answer": None,
        "explanation": "Assesses performance confidence and anxiety.",
        "parameter_tag": "exam_confidence"
    }
]
