import sys
import os
from datetime import date, timedelta
from database import init_db, get_connection, update_overdue_statuses
from services.auth_service import create_admin, hash_password

SAMPLE_ADMIN = {
    'username': os.environ.get('ADMIN_USERNAME', 'admin'),
    'email': os.environ.get('ADMIN_EMAIL', 'admin@libraverse.io'),
    'password': os.environ.get('ADMIN_PASSWORD', 'Admin@LibraVerse2026'),
    'full_name': os.environ.get('ADMIN_FULL_NAME', 'Chief Librarian Lyra'),
    'role': 'admin'
}

SAMPLE_BOOKS = [
    {
        'isbn': '978-0132350884',
        'title': 'Clean Code: A Handbook of Agile Software Craftsmanship',
        'author': 'Robert C. Martin',
        'category': 'Programming',
        'publisher': 'Prentice Hall',
        'publication_year': 2008,
        'total_copies': 6,
        'available_copies': 4,
        'description': 'Even bad code can function. But if code isn\'t clean, it can bring a development organization to its knees. Every year, countless hours and significant resources are lost because of poorly written code. But it doesn\'t have to be that way.',
        'cover_url': 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0201616224',
        'title': 'The Pragmatic Programmer: Your Journey To Mastery',
        'author': 'David Thomas, Andrew Hunt',
        'category': 'Programming',
        'publisher': 'Addison-Wesley',
        'publication_year': 1999,
        'total_copies': 5,
        'available_copies': 3,
        'description': 'One of the most significant books in modern software engineering. It examines the core of what it means to be a modern software developer, cutting through the technical trivia.',
        'cover_url': 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0262033848',
        'title': 'Introduction to Algorithms (CLRS)',
        'author': 'Thomas H. Cormen, Charles E. Leiserson',
        'category': 'Programming',
        'publisher': 'MIT Press',
        'publication_year': 2009,
        'total_copies': 4,
        'available_copies': 2,
        'description': 'Comprehensive textbook on computer algorithms, covering a broad spectrum of data structures, graph theory, dynamic programming, and computational complexity.',
        'cover_url': 'https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-1449355730',
        'title': 'Learning Python: Powerful Object-Oriented Programming',
        'author': 'Mark Lutz',
        'category': 'Programming',
        'publisher': 'O\'Reilly Media',
        'publication_year': 2013,
        'total_copies': 7,
        'available_copies': 5,
        'description': 'Get a comprehensive, in-depth introduction to the core Python language with this hands-on, self-paced tutorial that helps you write efficient, high-quality code.',
        'cover_url': 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0134685991',
        'title': 'Effective Java (3rd Edition)',
        'author': 'Joshua Bloch',
        'category': 'Programming',
        'publisher': 'Addison-Wesley',
        'publication_year': 2018,
        'total_copies': 4,
        'available_copies': 4,
        'description': 'A definitive guide to best practices in Java platform design and programming, filled with actionable architectural advice from one of Java\'s chief architects.',
        'cover_url': 'https://images.unsplash.com/photo-1537498425277-c283d32ef9db?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0141977225',
        'title': 'Life 3.0: Being Human in the Age of Artificial Intelligence',
        'author': 'Max Tegmark',
        'category': 'Technology',
        'publisher': 'Penguin Books',
        'publication_year': 2017,
        'total_copies': 6,
        'available_copies': 4,
        'description': 'Explores the future of intelligence, superintelligent AI, automated consciousness, and how society can prepare for the most disruptive technological breakthrough in history.',
        'cover_url': 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-1501139154',
        'title': 'Superintelligence: Paths, Dangers, Strategies',
        'author': 'Nick Bostrom',
        'category': 'Technology',
        'publisher': 'Oxford University Press',
        'publication_year': 2014,
        'total_copies': 4,
        'available_copies': 2,
        'description': 'What happens when machine brains surpass human brains in general intelligence? Bostrom lays out the existential foundation for alignment and safety.',
        'cover_url': 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0062316097',
        'title': 'Sapiens: A Brief History of Humankind',
        'author': 'Yuval Noah Harari',
        'category': 'History',
        'publisher': 'Harper',
        'publication_year': 2015,
        'total_copies': 8,
        'available_copies': 5,
        'description': 'From a renowned historian comes a groundbreaking narrative of humanity\'s creation and evolution, exploring the ways in which biology and history have defined us.',
        'cover_url': 'https://images.unsplash.com/photo-1461360370896-922624d12aa1?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0062464316',
        'title': 'Homo Deus: A Brief History of Tomorrow',
        'author': 'Yuval Noah Harari',
        'category': 'History',
        'publisher': 'Harper',
        'publication_year': 2017,
        'total_copies': 5,
        'available_copies': 4,
        'description': 'Harari looks ahead to future worlds, unravelling dreams and nightmares that will shape the 21st century: from overcoming death to creating artificial life.',
        'cover_url': 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0385504201',
        'title': 'A Short History of Nearly Everything',
        'author': 'Bill Bryson',
        'category': 'Science',
        'publisher': 'Broadway Books',
        'publication_year': 2003,
        'total_copies': 6,
        'available_copies': 3,
        'description': 'One of the world\'s most beloved writers takes on the ultimate challenge: understanding how we got from there being nothing at all to there being us.',
        'cover_url': 'https://images.unsplash.com/photo-1507413245164-6160d8298b31?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0345539434',
        'title': 'Cosmos',
        'author': 'Carl Sagan',
        'category': 'Science',
        'publisher': 'Ballantine Books',
        'publication_year': 1980,
        'total_copies': 5,
        'available_copies': 4,
        'description': 'The legendary astronomer retraces fifteen billion years of cosmic evolution, presenting a spellbinding journey into humanity\'s exploration of the universe.',
        'cover_url': 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0553380163',
        'title': 'A Brief History of Time',
        'author': 'Stephen Hawking',
        'category': 'Science',
        'publisher': 'Bantam Books',
        'publication_year': 1988,
        'total_copies': 5,
        'available_copies': 2,
        'description': 'A landmark volume in science writing by one of the greatest minds of our time, exploring black holes, space-time frontiers, and the general theory of relativity.',
        'cover_url': 'https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0441172719',
        'title': 'Dune',
        'author': 'Frank Herbert',
        'category': 'Fiction',
        'publisher': 'Chilton Books',
        'publication_year': 1965,
        'total_copies': 6,
        'available_copies': 3,
        'description': 'Set on the desert planet Arrakis, Dune is the story of Paul Atreides, heir to a noble family tasked with ruling an inhospitable world where the only thing of value is the spice melange.',
        'cover_url': 'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0451524935',
        'title': '1984',
        'author': 'George Orwell',
        'category': 'Fiction',
        'publisher': 'Secker & Warburg',
        'publication_year': 1949,
        'total_copies': 7,
        'available_copies': 5,
        'description': 'The classic dystopia portraying Oceania, a totalitarian regime that monitors every move through Big Brother and the Thought Police.',
        'cover_url': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0547928227',
        'title': 'The Hobbit',
        'author': 'J.R.R. Tolkien',
        'category': 'Fiction',
        'publisher': 'George Allen & Unwin',
        'publication_year': 1937,
        'total_copies': 5,
        'available_copies': 4,
        'description': 'Bilbo Baggins is a hobbit who enjoys a comfortable, unambitious life, until the wizard Gandalf and a company of dwarves arrive on his threshold to embark on an epic quest.',
        'cover_url': 'https://images.unsplash.com/photo-1532012164546-f432f2e3edd9?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0307277671',
        'title': 'The Da Vinci Code',
        'author': 'Dan Brown',
        'category': 'Mystery',
        'publisher': 'Doubleday',
        'publication_year': 2003,
        'total_copies': 5,
        'available_copies': 3,
        'description': 'While in Paris, Harvard symbologist Robert Langdon is awakened by an urgent phone call: the elderly curator of the Louvre has been murdered inside the museum.',
        'cover_url': 'https://images.unsplash.com/photo-1476275466078-4007374efbbe?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0316017923',
        'title': 'The Girl with the Dragon Tattoo',
        'author': 'Stieg Larsson',
        'category': 'Mystery',
        'publisher': 'Norstedts Förlag',
        'publication_year': 2005,
        'total_copies': 4,
        'available_copies': 3,
        'description': 'A spellbinding thriller pairing investigative journalist Mikael Blomkvist with the brilliant, tattooed hacker Lisbeth Salander.',
        'cover_url': 'https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0060555665',
        'title': 'The Intelligent Investor',
        'author': 'Benjamin Graham',
        'category': 'Business',
        'publisher': 'Harper Business',
        'publication_year': 1949,
        'total_copies': 6,
        'available_copies': 4,
        'description': 'The greatest investment advisor of the twentieth century taught and inspired people worldwide with his philosophy of value investing.',
        'cover_url': 'https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0670921607',
        'title': 'Zero to One: Notes on Startups, or How to Build the Future',
        'author': 'Peter Thiel, Blake Masters',
        'category': 'Business',
        'publisher': 'Crown Business',
        'publication_year': 2014,
        'total_copies': 5,
        'available_copies': 3,
        'description': 'The great secret of our time is that there are still uncharted frontiers to explore and new inventions to create. Doing what we already know takes the world from 1 to n.',
        'cover_url': 'https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0735211292',
        'title': 'Atomic Habits: An Easy & Proven Way to Build Good Habits',
        'author': 'James Clear',
        'category': 'Personal Development',
        'publisher': 'Avery',
        'publication_year': 2018,
        'total_copies': 8,
        'available_copies': 5,
        'description': 'No matter your goals, Atomic Habits offers a proven framework for improving every day by mastering the tiny behaviors that lead to remarkable results.',
        'cover_url': 'https://images.unsplash.com/photo-1544717305-2782549b5136?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-1501110368',
        'title': 'Deep Work: Rules for Focused Success in a Distracted World',
        'author': 'Cal Newport',
        'category': 'Personal Development',
        'publisher': 'Grand Central Publishing',
        'publication_year': 2016,
        'total_copies': 6,
        'available_copies': 4,
        'description': 'Deep work is the ability to focus without distraction on a cognitively demanding task. It is a super power in our increasingly competitive twenty-first century economy.',
        'cover_url': 'https://images.unsplash.com/photo-1499750310107-5fef28a66643?auto=format&fit=crop&w=600&q=80'
    },
    {
        'isbn': '978-0062457714',
        'title': 'The Subtle Art of Not Giving a F*ck',
        'author': 'Mark Manson',
        'category': 'Personal Development',
        'publisher': 'HarperOne',
        'publication_year': 2016,
        'total_copies': 5,
        'available_copies': 4,
        'description': 'A counterintuitive approach to living a good life by confronting the raw, refreshing reality of limitations and choosing what truly matters.',
        'cover_url': 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=600&q=80'
    }
]

SAMPLE_MEMBERS = [
    {
        'full_name': 'Aria Vance',
        'email': 'aria.vance@quantummail.io',
        'phone': '+1 (555) 234-5678',
        'membership_status': 'Active',
        'registration_date': '2026-01-15'
    },
    {
        'full_name': 'Kaelen Drake',
        'email': 'kaelen.drake@cybertech.edu',
        'phone': '+1 (555) 345-6789',
        'membership_status': 'Active',
        'registration_date': '2026-02-10'
    },
    {
        'full_name': 'Seraphina Lin',
        'email': 's.lin@matrixresearch.org',
        'phone': '+1 (555) 456-7890',
        'membership_status': 'Active',
        'registration_date': '2026-03-01'
    },
    {
        'full_name': 'Damian Cross',
        'email': 'damian.cross@deepnet.com',
        'phone': '+1 (555) 567-8901',
        'membership_status': 'Active',
        'registration_date': '2026-04-12'
    },
    {
        'full_name': 'Elena Rostova',
        'email': 'elena.rostova@stellaris.dev',
        'phone': '+1 (555) 678-9012',
        'membership_status': 'Active',
        'registration_date': '2026-05-20'
    },
    {
        'full_name': 'Marcus Aurelius Sterling',
        'email': 'marcus.sterling@consortium.org',
        'phone': '+1 (555) 789-0123',
        'membership_status': 'Active',
        'registration_date': '2026-06-05'
    },
    {
        'full_name': 'Nova Chen',
        'email': 'nova.chen@starlight.io',
        'phone': '+1 (555) 890-1234',
        'membership_status': 'Active',
        'registration_date': '2026-07-14'
    },
    {
        'full_name': 'Rowan Thorne',
        'email': 'rowan.thorne@archon.co',
        'phone': '+1 (555) 901-2345',
        'membership_status': 'Suspended',
        'registration_date': '2026-08-01'
    }
]

def seed_database(db_path=None, reset=False):
    """Seed the SQLite database with comprehensive sample data safely."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if reset:
        print("[!] Reset flag passed. Clearing existing data...")
        cursor.execute("DELETE FROM borrowings")
        cursor.execute("DELETE FROM books")
        cursor.execute("DELETE FROM members")
        cursor.execute("DELETE FROM admins")
        conn.commit()

    # 1. Admin setup
    cursor.execute("SELECT id FROM admins WHERE username = ?", (SAMPLE_ADMIN['username'],))
    admin_row = cursor.fetchone()
    if not admin_row:
        print(f"[+] Creating default administrator '{SAMPLE_ADMIN['username']}'...")
        cursor.execute("""
            INSERT INTO admins (username, email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        """, (
            SAMPLE_ADMIN['username'],
            SAMPLE_ADMIN['email'],
            hash_password(SAMPLE_ADMIN['password']),
            SAMPLE_ADMIN['full_name'],
            SAMPLE_ADMIN['role']
        ))
        conn.commit()
    else:
        print(f"[*] Administrator '{SAMPLE_ADMIN['username']}' already exists.")

    # 2. Books setup
    inserted_books = 0
    for b in SAMPLE_BOOKS:
        cursor.execute("SELECT id FROM books WHERE isbn = ?", (b['isbn'],))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO books (isbn, title, author, category, publisher, publication_year,
                                   total_copies, available_copies, description, cover_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                b['isbn'], b['title'], b['author'], b['category'], b['publisher'],
                b['publication_year'], b['total_copies'], b['available_copies'],
                b['description'], b['cover_url']
            ))
            inserted_books += 1
    conn.commit()
    print(f"[*] Books checked. {inserted_books} new books inserted.")

    # 3. Members setup
    inserted_members = 0
    for m in SAMPLE_MEMBERS:
        cursor.execute("SELECT id FROM members WHERE LOWER(email) = ?", (m['email'].lower(),))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO members (full_name, email, phone, membership_status, registration_date)
                VALUES (?, ?, ?, ?, ?)
            """, (
                m['full_name'], m['email'], m['phone'], m['membership_status'], m['registration_date']
            ))
            inserted_members += 1
    conn.commit()
    print(f"[*] Members checked. {inserted_members} new members inserted.")

    # 4. Borrowing Transactions setup
    cursor.execute("SELECT COUNT(*) as count FROM borrowings")
    borrow_count = cursor.fetchone()['count']

    if borrow_count == 0:
        print("[+] Creating realistic sample borrowing records...")
        # Get book and member IDs
        cursor.execute("SELECT id, title FROM books ORDER BY id ASC")
        books = cursor.fetchall()
        cursor.execute("SELECT id, full_name FROM members ORDER BY id ASC")
        members = cursor.fetchall()

        today = date.today()

        # Build realistic distribution of past returned, currently issued, and overdue borrowings
        transactions_data = [
            # Returned on time
            {
                'book_idx': 0, 'member_idx': 0,
                'issue_date': (today - timedelta(days=60)).isoformat(),
                'due_date': (today - timedelta(days=46)).isoformat(),
                'return_date': (today - timedelta(days=48)).isoformat(),
                'status': 'Returned', 'overdue_days': 0, 'fine_amount': 0.0
            },
            # Returned with 3 days overdue
            {
                'book_idx': 1, 'member_idx': 1,
                'issue_date': (today - timedelta(days=50)).isoformat(),
                'due_date': (today - timedelta(days=36)).isoformat(),
                'return_date': (today - timedelta(days=33)).isoformat(),
                'status': 'Returned', 'overdue_days': 3, 'fine_amount': 4.50
            },
            # Returned on time
            {
                'book_idx': 2, 'member_idx': 2,
                'issue_date': (today - timedelta(days=45)).isoformat(),
                'due_date': (today - timedelta(days=31)).isoformat(),
                'return_date': (today - timedelta(days=32)).isoformat(),
                'status': 'Returned', 'overdue_days': 0, 'fine_amount': 0.0
            },
            # Returned on time
            {
                'book_idx': 3, 'member_idx': 3,
                'issue_date': (today - timedelta(days=40)).isoformat(),
                'due_date': (today - timedelta(days=26)).isoformat(),
                'return_date': (today - timedelta(days=28)).isoformat(),
                'status': 'Returned', 'overdue_days': 0, 'fine_amount': 0.0
            },
            # Returned with 5 days overdue
            {
                'book_idx': 5, 'member_idx': 4,
                'issue_date': (today - timedelta(days=35)).isoformat(),
                'due_date': (today - timedelta(days=21)).isoformat(),
                'return_date': (today - timedelta(days=16)).isoformat(),
                'status': 'Returned', 'overdue_days': 5, 'fine_amount': 7.50
            },
            # Currently Issued (due in 5 days)
            {
                'book_idx': 0, 'member_idx': 1,
                'issue_date': (today - timedelta(days=9)).isoformat(),
                'due_date': (today + timedelta(days=5)).isoformat(),
                'return_date': None,
                'status': 'Issued', 'overdue_days': 0, 'fine_amount': 0.0
            },
            # Currently Issued (due in 10 days)
            {
                'book_idx': 1, 'member_idx': 2,
                'issue_date': (today - timedelta(days=4)).isoformat(),
                'due_date': (today + timedelta(days=10)).isoformat(),
                'return_date': None,
                'status': 'Issued', 'overdue_days': 0, 'fine_amount': 0.0
            },
            # Currently Issued (due in 7 days)
            {
                'book_idx': 6, 'member_idx': 3,
                'issue_date': (today - timedelta(days=7)).isoformat(),
                'due_date': (today + timedelta(days=7)).isoformat(),
                'return_date': None,
                'status': 'Issued', 'overdue_days': 0, 'fine_amount': 0.0
            },
            # Currently Issued (due in 2 days)
            {
                'book_idx': 7, 'member_idx': 0,
                'issue_date': (today - timedelta(days=12)).isoformat(),
                'due_date': (today + timedelta(days=2)).isoformat(),
                'return_date': None,
                'status': 'Issued', 'overdue_days': 0, 'fine_amount': 0.0
            },
            # Overdue by 4 days
            {
                'book_idx': 2, 'member_idx': 4,
                'issue_date': (today - timedelta(days=18)).isoformat(),
                'due_date': (today - timedelta(days=4)).isoformat(),
                'return_date': None,
                'status': 'Overdue', 'overdue_days': 4, 'fine_amount': 6.00
            },
            # Overdue by 8 days
            {
                'book_idx': 5, 'member_idx': 5,
                'issue_date': (today - timedelta(days=22)).isoformat(),
                'due_date': (today - timedelta(days=8)).isoformat(),
                'return_date': None,
                'status': 'Overdue', 'overdue_days': 8, 'fine_amount': 12.00
            },
            # Returned
            {
                'book_idx': 9, 'member_idx': 6,
                'issue_date': (today - timedelta(days=25)).isoformat(),
                'due_date': (today - timedelta(days=11)).isoformat(),
                'return_date': (today - timedelta(days=12)).isoformat(),
                'status': 'Returned', 'overdue_days': 0, 'fine_amount': 0.0
            },
            # Returned
            {
                'book_idx': 11, 'member_idx': 0,
                'issue_date': (today - timedelta(days=30)).isoformat(),
                'due_date': (today - timedelta(days=16)).isoformat(),
                'return_date': (today - timedelta(days=18)).isoformat(),
                'status': 'Returned', 'overdue_days': 0, 'fine_amount': 0.0
            },
            # Currently Issued
            {
                'book_idx': 11, 'member_idx': 6,
                'issue_date': (today - timedelta(days=5)).isoformat(),
                'due_date': (today + timedelta(days=9)).isoformat(),
                'return_date': None,
                'status': 'Issued', 'overdue_days': 0, 'fine_amount': 0.0
            },
            # Currently Issued
            {
                'book_idx': 12, 'member_idx': 2,
                'issue_date': (today - timedelta(days=2)).isoformat(),
                'due_date': (today + timedelta(days=12)).isoformat(),
                'return_date': None,
                'status': 'Issued', 'overdue_days': 0, 'fine_amount': 0.0
            }
        ]

        for t in transactions_data:
            book_id = books[t['book_idx']]['id']
            member_id = members[t['member_idx']]['id']
            cursor.execute("""
                INSERT INTO borrowings (book_id, member_id, issue_date, due_date, return_date, status, overdue_days, fine_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                book_id, member_id, t['issue_date'], t['due_date'],
                t['return_date'], t['status'], t['overdue_days'], t['fine_amount']
            ))
        conn.commit()
        print(f"[+] {len(transactions_data)} realistic borrowing transactions seeded.")
    else:
        print(f"[*] Borrowing records already present ({borrow_count} records).")

    conn.close()

    # Recalculate and synchronize exact overdue days and stock consistency
    update_overdue_statuses(db_path)
    print("[OK] LibraVerse database initialized and seeded successfully!")

if __name__ == '__main__':
    reset_flag = '--reset' in sys.argv
    seed_database(reset=reset_flag)
